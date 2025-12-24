"""
Runtime execution abstraction for multi-language support.

Provides a pluggable runtime system that allows PCards to execute
in different language environments (Python, JavaScript, Rust, C, etc.)

=============================================================================
REFACTORED MODULE - All implementations now in mcard.ptr.core.runtimes
=============================================================================

This file now serves as a backward-compatible re-export layer.
All runtime implementations have been moved to modular files:

    mcard/ptr/core/runtimes/
    ├── base.py           # RuntimeType, BoundaryType, RuntimeExecutor, SubprocessRuntime
    ├── python.py         # PythonRuntime
    ├── javascript.py     # JavaScriptRuntime  
    ├── binary.py         # BinaryRuntime, RustRuntime, CRuntime
    ├── script.py         # ScriptRuntime, LeanRuntime, RRuntime, JuliaRuntime
    ├── lambda_calc.py    # LambdaRuntimeExecutor
    └── factory.py        # RuntimeFactory

Direct imports from this module are supported for backward compatibility:
    from mcard.ptr.core.runtime import PythonRuntime, RuntimeFactory

Recommended usage for new code:
    from mcard.ptr.core.runtimes import PythonRuntime, RuntimeFactory

"""

# ─────────────────────────────────────────────────────────────────────────────
# Re-exports from runtimes module (backward compatibility)
# ─────────────────────────────────────────────────────────────────────────────

from .runtimes import (
    # Enums
    RuntimeType,
    BoundaryType,
    
    # Base Classes
    RuntimeExecutor,
    SubprocessRuntime,
    
    # Configuration Constants
    DEFAULT_TIMEOUT,
    LEAN_TIMEOUT,
    JULIA_TIMEOUT,
    R_TIMEOUT,
    RUNTIME_CONFIG,
    
    # Runtime Implementations
    PythonRuntime,
    JavaScriptRuntime,
    BinaryRuntime,
    RustRuntime,
    CRuntime,
    ScriptRuntime,
    LeanRuntime,
    RRuntime,
    JuliaRuntime,
    LambdaRuntimeExecutor,
    
    # Factory
    RuntimeFactory,
)

# Legacy constant (kept for backward compatibility)
MODULE_URI_PREFIX = 'module://'

# Legacy imports for sandboxing (kept for backward compatibility)
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

# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

__all__ = [
    # Enums
    'RuntimeType',
    'BoundaryType',
    
    # Base Classes  
    'RuntimeExecutor',
    'SubprocessRuntime',
    
    # Configuration
    'DEFAULT_TIMEOUT',
    'LEAN_TIMEOUT',
    'JULIA_TIMEOUT', 
    'R_TIMEOUT',
    'RUNTIME_CONFIG',
    'ALLOWED_IMPORTS',
    'SAFE_BUILTINS',
    'MODULE_URI_PREFIX',
    
    # Runtimes
    'PythonRuntime',
    'JavaScriptRuntime',
    'BinaryRuntime',
    'RustRuntime',
    'CRuntime',
    'ScriptRuntime',
    'LeanRuntime',
    'RRuntime',
    'JuliaRuntime',
    'LambdaRuntimeExecutor',
    
    # Factory
    'RuntimeFactory',
]
