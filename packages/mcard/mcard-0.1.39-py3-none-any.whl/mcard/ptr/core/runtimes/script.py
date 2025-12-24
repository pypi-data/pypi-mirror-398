"""
Script-based runtimes (Lean, R, Julia).

These runtimes execute script files via interpreter subprocess.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Union

from mcard import MCard

from .base import SubprocessRuntime, RUNTIME_CONFIG, LEAN_TIMEOUT, R_TIMEOUT, JULIA_TIMEOUT


class ScriptRuntime(SubprocessRuntime):
    """Base class for runtimes that execute script files."""
    
    file_key = 'code_file'
    run_args: List[str] = []
    
    def execute(self, impl: Dict[str, Any], target: MCard, ctx: Dict[str, Any]) -> Any:
        code_file = impl.get(self.file_key)
        if not code_file:
            return f"Error: No {self.runtime_name} code file provided"
        
        # Normalize command to list
        base_cmd = self.command if isinstance(self.command, list) else [self.command]
        
        cmd = base_cmd + self.run_args + [code_file, json.dumps(ctx)]
        return self._run_subprocess(cmd, target, ctx, self.timeout)


class LeanRuntime(ScriptRuntime):
    """Lean 4 runtime executor."""
    runtime_name = "Lean"
    run_args = ['--run']
    timeout = LEAN_TIMEOUT
    
    def __init__(self):
        super().__init__()
        # Dynamic check for elan to support specific toolchains (e.g. v4.25.2)
        # Matches JS implementation in mcard-js/src/ptr/node/runtimes/lean.ts
        elan_path = Path.home() / '.elan' / 'bin' / 'elan'
        
        # Check explicit environment variable first
        env_lean_cmd = RUNTIME_CONFIG.get('lean', {}).get('command')
        
        if env_lean_cmd and env_lean_cmd != 'lean':
             # Use configured command if it's specific
            self.command = env_lean_cmd
        elif elan_path.exists():
            # Use elan to ensure we use the same version as JS tests
            # 'elan run' avoids downloading 'stable' if we pin to v4.25.2 match JS
            self.command = [str(elan_path), 'run', 'leanprover/lean4:v4.25.2', 'lean']
        else:
            # Fallback to system lean (subject to lean-toolchain file)
            self.command = 'lean'
    
    def validate_environment(self) -> bool:
        # Lean 4 takes longer to initialize, use extended timeout
        return self._check_command(self.command, self.version_flag, timeout=30)
    
    def execute(self, impl: Dict[str, Any], target: MCard, ctx: Dict[str, Any]) -> Any:
        """Execute Lean script, passing input as the argument."""
        code_file = impl.get(self.file_key)
        if not code_file:
            return f"Error: No {self.runtime_name} code file provided"
        
        # Determine what to pass as the argument:
        # 1. If context has 'op', 'a', 'b' keys (polyglot mode), use context as JSON
        # 2. Otherwise, use target content (standalone CLM mode)
        if ctx and ('op' in ctx or 'a' in ctx or 'n' in ctx):
            # Polyglot/advanced mode - context contains the actual input data
            input_data = json.dumps(ctx)
        else:
            # Standalone CLM mode - target content is the JSON input
            input_data = target.get_content().decode('utf-8', errors='ignore')
        
        # Normalize command to list
        base_cmd = self.command if isinstance(self.command, list) else [self.command]
        
        cmd = base_cmd + self.run_args + [code_file, input_data]
        return self._run_subprocess(cmd, target, ctx, self.timeout)


class RRuntime(ScriptRuntime):
    """R runtime executor."""
    runtime_name = "R"
    command = RUNTIME_CONFIG.get('r', {}).get('command', 'Rscript')
    timeout = R_TIMEOUT


class JuliaRuntime(ScriptRuntime):
    """Julia runtime executor."""
    runtime_name = "Julia"
    command = RUNTIME_CONFIG.get('julia', {}).get('command', 'julia')
    timeout = JULIA_TIMEOUT
