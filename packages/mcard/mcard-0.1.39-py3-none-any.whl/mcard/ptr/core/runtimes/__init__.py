"""
Runtimes Module for PTR
========================

This module provides modular runtime executor implementations.

Organization:
- base.py: Core abstractions (RuntimeExecutor, SubprocessRuntime, enums)
- python.py: PythonRuntime (in-process Python execution)
- javascript.py: JavaScriptRuntime (Node.js/Deno execution)
- binary.py: BinaryRuntime, RustRuntime, CRuntime
- script.py: ScriptRuntime, LeanRuntime, RRuntime, JuliaRuntime
- lambda_calc.py: LambdaRuntimeExecutor
- factory.py: RuntimeFactory

For backward compatibility, the main runtime.py re-exports all classes.
"""

from .base import (
    RuntimeType,
    BoundaryType,
    RuntimeExecutor,
    SubprocessRuntime,
    DEFAULT_TIMEOUT,
    LEAN_TIMEOUT,
    JULIA_TIMEOUT,
    R_TIMEOUT,
    RUNTIME_CONFIG,
)

from .python import PythonRuntime
from .javascript import JavaScriptRuntime
from .binary import BinaryRuntime, RustRuntime, CRuntime
from .script import ScriptRuntime, LeanRuntime, RRuntime, JuliaRuntime
from .lambda_calc import LambdaRuntimeExecutor
from .factory import RuntimeFactory

__all__ = [
    # Enums
    'RuntimeType',
    'BoundaryType',
    # Base classes
    'RuntimeExecutor',
    'SubprocessRuntime',
    # Configuration
    'DEFAULT_TIMEOUT',
    'LEAN_TIMEOUT',
    'JULIA_TIMEOUT',
    'R_TIMEOUT',
    'RUNTIME_CONFIG',
    # Runtime implementations
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
