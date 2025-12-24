"""
Python runtime executor.

Executes Python code directly in-process with sandboxing.
"""

import importlib
import json
from typing import Any, Callable, Dict

from mcard import MCard

from .base import RuntimeExecutor, RUNTIME_CONFIG

# Module URI prefix for dynamic module imports
MODULE_URI_PREFIX = 'module://'

# Import sandbox configuration
try:
    from mcard.config.settings import settings as _settings
    ALLOWED_IMPORTS = _settings.ptr.allowed_imports
    SAFE_BUILTINS = _settings.ptr.safe_builtins
except ImportError:
    ALLOWED_IMPORTS = {
        'math': 'math', 'json': 'json', 'yaml': 'yaml', 'pathlib': 'pathlib',
        'typing': 'typing', 'hashlib': 'hashlib', 'mcard': 'mcard',
        'os': 'os', 'time': 'time', 'random': 'random', 'logging': 'logging',
    }
    SAFE_BUILTINS = {
        'int', 'float', 'str', 'len', 'range', 'list', 'dict', 'tuple', 'set',
        'abs', 'round', 'max', 'min', 'sum', 'sorted', 'enumerate', 'zip',
        'ValueError', 'Exception', '__build_class__', 'super', 'open',
        'all', 'any', 'bool', 'isinstance', 'bytes', 'print', 'globals',
    }


class PythonRuntime(RuntimeExecutor):
    """Python runtime executor - executes Python code directly in-process."""
    
    # Operation handlers mapping
    OPERATIONS: Dict[str, Callable] = {}
    
    # Compilation cache for sandboxed execution
    _compilation_cache: Dict[str, Any] = {}
    
    def __init__(self):
        super().__init__()
        # Import operations from the extracted operations module
        from ..operations import DEFAULT_OPERATIONS
        
        # Register built-in operations from module
        self.OPERATIONS = DEFAULT_OPERATIONS.copy()
        
        # Add custom operation handler (requires self reference for sandboxing)
        self.OPERATIONS['custom'] = self._op_custom
    
    def execute(self, concrete_impl: Dict[str, Any], target: MCard, context: Dict[str, Any]) -> Any:
        # Check for module:// syntax first
        code_file = concrete_impl.get('code_file', '')
        if code_file.startswith(MODULE_URI_PREFIX):
            return self._execute_module_logic(code_file, concrete_impl, target, context)
        
        # Determine operation
        operation = concrete_impl.get('process', concrete_impl.get('action', concrete_impl.get('operation')))
        if not operation:
            operation = concrete_impl.get('builtin')
        
        if not operation:
            # Auto-detect custom operation if code is present
            if 'code_file' in concrete_impl or 'code' in concrete_impl:
                operation = 'custom'
            else:
                operation = 'identity'
                
        handler = self.OPERATIONS.get(operation)
        
        if handler:
            return handler(concrete_impl, target, context)
        return f"Executed {operation} on {target.hash}"
    
    # ─── Custom Operation ──────────────────────────────────────────────────────
    
    def _op_custom(self, impl: Dict, target: MCard, ctx: Dict) -> Any:
        code_file = impl.get('code_file', '')
        if code_file.startswith(MODULE_URI_PREFIX):
            return self._execute_module_logic(code_file, impl, target, ctx)
        
        code = impl.get('code', '')
        if not code:
            return "Error: No code provided"
        
        return self._exec_sandboxed(code, impl, target, ctx)
    
    # ─── Sandboxed Execution ───────────────────────────────────────────────────
    
    def _make_safe_import(self) -> Callable:
        """Create a safe import function."""
        def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name in ALLOWED_IMPORTS:
                return importlib.import_module(name)
            raise ImportError(f"Import of '{name}' is not allowed")
        return safe_import
    
    def _make_namespace(self, target: MCard, context: Dict) -> Dict:
        """Create a sandboxed namespace for code execution."""
        import math
        import builtins as builtins_module
        
        # Build safe builtins dict from the builtins module
        safe_builtins = {}
        for name in SAFE_BUILTINS:
            if hasattr(builtins_module, name):
                safe_builtins[name] = getattr(builtins_module, name)
        
        safe_builtins['__import__'] = self._make_safe_import()
        safe_builtins['__build_class__'] = builtins_module.__build_class__
        
        return {
            '__builtins__': safe_builtins,
            'target': target.get_content(),
            'context': context,
            'result': None,
            'math': math,
            '__name__': '__clm_runtime__'
        }
    
    def _exec_sandboxed(self, code: str, impl: Dict, target: MCard, ctx: Dict) -> Any:
        """Execute code in a sandboxed namespace with compilation caching."""
        namespace = self._make_namespace(target, ctx)
        
        try:
            # Use cached code object if available to avoid re-parsing
            if code not in self._compilation_cache:
                self._compilation_cache[code] = compile(code, '<string>', 'exec')
            
            exec(self._compilation_cache[code], namespace)
            
            entry_point = impl.get('entry_point')
            if entry_point:
                return self._call_entry_point(namespace, entry_point, impl, target, ctx)
            return namespace.get('result')
        except Exception as e:
            return f"Error executing Python code: {e}"
    
    def _call_entry_point(self, ns: Dict, entry: str, impl: Dict, target: MCard, ctx: Dict) -> Any:
        """Call a function defined in namespace."""
        if entry not in ns or not callable(ns[entry]):
            return f"Error: Entry point '{entry}' not found or not callable. Keys: {list(ns.keys())}"
        
        func = ns[entry]
        arg = self._prepare_argument(impl, target, ctx)
        return func(arg)
    
    def _prepare_argument(self, impl: Dict, target: MCard, ctx: Dict) -> Any:
        """Prepare argument for entry point function."""
        inputs_def = impl.get('implementation', {}).get('inputs', {})
        
        # If context has operation or params keys, the entry point likely expects context
        if ctx.get('operation') or ctx.get('params') or ctx.get('op'):
            combined = ctx.copy()
            content = target.get_content()
            if isinstance(content, bytes):
                try:
                    content = content.decode('utf-8')
                except:
                    pass
            combined['value'] = content
            combined['__input_content__'] = content
            return combined
        
        if not inputs_def:
            return target.get_content()
        
        input_name = list(inputs_def.keys())[0]
        input_type = inputs_def[input_name]
        
        if input_name == 'context':
            return ctx
        
        raw = target.get_content()
        converters = {
            'float': lambda: float(raw.decode('utf-8')),
            'int': lambda: int(raw.decode('utf-8')),
            'str': lambda: raw.decode('utf-8'),
        }
        
        try:
            return converters.get(input_type, lambda: raw)()
        except Exception:
            return raw
    
    # ─── Module Logic ──────────────────────────────────────────────────────────
    
    def _execute_module_logic(self, uri: str, impl: Dict, target: MCard, ctx: Dict) -> Any:
        """Execute logic imported from a Python module."""
        path = uri.replace(MODULE_URI_PREFIX, '')
        module_name, func_name = (path.split(':', 1) if ':' in path 
                                  else (path, impl.get('entry_point', 'logic')))
        
        try:
            module = importlib.import_module(module_name)
            func = getattr(module, func_name)
            if not callable(func):
                return f"Error: {func_name} in {module_name} is not callable"
            
            arg = target.get_content().decode('utf-8') if hasattr(target, 'get_content') else target
            return func(arg)
        except ImportError as e:
            return f"Error importing module {module_name}: {e}"
        except AttributeError:
            return f"Error: Function {func_name} not found in {module_name}"
        except Exception as e:
            return f"Error executing module logic: {e}"
    
    def validate_environment(self) -> bool:
        return True
    
    def get_runtime_status(self) -> Dict[str, Any]:
        import sys
        return {
            'available': True,
            'version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'command': RUNTIME_CONFIG.get('python', {}).get('command', 'python3'),
            'details': f'Python {sys.version}'
        }
