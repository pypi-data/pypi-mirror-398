"""
Binary-based runtimes (Rust, C).

These runtimes execute compiled binaries via subprocess.
"""

import json
from typing import Any, Dict

from mcard import MCard

from .base import SubprocessRuntime, RUNTIME_CONFIG


class BinaryRuntime(SubprocessRuntime):
    """Base class for runtimes that execute compiled binaries."""
    
    def execute(self, impl: Dict[str, Any], target: MCard, ctx: Dict[str, Any]) -> Any:
        binary_path = impl.get('binary_path')
        if not binary_path:
            return f"Error: No {self.runtime_name} binary path provided"
        return self._run_subprocess([binary_path, json.dumps(ctx)], target, ctx)


class RustRuntime(BinaryRuntime):
    """Rust runtime executor - executes via compiled binary or WASM."""
    
    runtime_name = "Rust"
    command = RUNTIME_CONFIG.get('rust', {}).get('command')
    
    def execute(self, impl: Dict[str, Any], target: MCard, ctx: Dict[str, Any]) -> Any:
        wasm_module = impl.get('wasm_module')
        if wasm_module:
            return self._execute_wasm(wasm_module, target, ctx)
        return super().execute(impl, target, ctx)
    
    def _execute_wasm(self, wasm_path: str, target: MCard, ctx: Dict) -> Any:
        """Execute WASM module using wasmtime."""
        try:
            from wasmtime import Store, Module, Linker, WasiConfig
            import tempfile, os
            
            store = Store()
            wasi = WasiConfig()
            wasi.inherit_stdout()
            wasi.inherit_stderr()
            wasi.argv = ["program_name", json.dumps(ctx)]
            
            # Create temp files for stdin/stdout
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_in:
                tmp_in.write(target.get_content().decode('utf-8'))
                in_path = tmp_in.name
            
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_out:
                out_path = tmp_out.name
            
            wasi.stdin_file = in_path
            wasi.stdout_file = out_path
            store.set_wasi(wasi)
            
            linker = Linker(store.engine)
            linker.define_wasi()
            
            module = Module.from_file(store.engine, wasm_path)
            instance = linker.instantiate(store, module)
            instance.exports(store)["_start"](store)
            
            with open(out_path, 'r') as f:
                output = f.read()
            
            os.unlink(in_path)
            os.unlink(out_path)
            return output
            
        except ImportError as e:
            return f"Error: wasmtime python library not installed or load failed: {e}"
        except Exception as e:
            return f"Error executing WASM: {e}"
    
    def validate_environment(self) -> bool:
        rust_ok = self._check_command('rustc', '--version')
        wasm_ok = False
        try:
            import wasmtime
            wasm_ok = True
        except ImportError:
            pass
        return rust_ok or wasm_ok


class CRuntime(BinaryRuntime):
    """C runtime executor - executes via compiled binary."""
    runtime_name = "C"
    command = None  # No compiler check needed
