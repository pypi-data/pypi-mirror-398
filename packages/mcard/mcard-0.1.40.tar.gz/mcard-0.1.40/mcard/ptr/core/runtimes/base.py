"""
Base classes for runtime executors.

This module provides the core abstractions for runtime execution:
- RuntimeType: Enum of supported runtimes
- BoundaryType: Enum for intrinsic/extrinsic execution
- RuntimeExecutor: Abstract base class for all runtimes
- SubprocessRuntime: Base class for runtimes that execute via subprocess
"""

import logging
import subprocess
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from mcard import MCard

# ─────────────────────────────────────────────────────────────────────────────
# Configuration Constants
# ─────────────────────────────────────────────────────────────────────────────

try:
    from mcard.config.settings import settings as _settings
    DEFAULT_TIMEOUT = _settings.ptr.default_timeout
    LEAN_TIMEOUT = _settings.ptr.lean_timeout
    JULIA_TIMEOUT = _settings.ptr.julia_timeout
    R_TIMEOUT = _settings.ptr.r_timeout
    RUNTIME_CONFIG = _settings.ptr.runtime_config
except ImportError:
    DEFAULT_TIMEOUT = 5
    LEAN_TIMEOUT = 30
    JULIA_TIMEOUT = 15
    R_TIMEOUT = 10
    RUNTIME_CONFIG = {
        'python': {'command': 'python3', 'version_flag': '--version'},
        'javascript': {'command': ['npx', 'tsx'], 'version_flag': '--version', 'eval_flag': '--eval'},
        'lean': {'command': 'lean', 'version_flag': '--version', 'run_flag': '--run'},
        'r': {'command': 'Rscript', 'version_flag': '--version'},
        'julia': {'command': 'julia', 'version_flag': '--version'},
        'rust': {'command': None},
        'c': {'command': None},
        'wasm': {'command': None},
    }


# ─────────────────────────────────────────────────────────────────────────────
# Runtime Types
# ─────────────────────────────────────────────────────────────────────────────

class RuntimeType(Enum):
    """Supported runtime types."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    RUST = "rust"
    C = "c"
    WASM = "wasm"
    LEAN = "lean"
    R = "r"
    JULIA = "julia"
    LLM = "llm"
    LAMBDA = "lambda"
    NETWORK = "network"


class BoundaryType(Enum):
    """CLM execution boundary type.
    
    Determines how a CLM is executed relative to the caller:
    
    INTRINSIC: Process runs within the same execution context (same process).
               Best for lightweight, trusted operations. No serialization overhead.
               
    EXTRINSIC: Process runs in a separate process/container/network.
               Required for untrusted code, language isolation, or distributed execution.
               Requires serialization/deserialization of inputs and outputs.
    """
    INTRINSIC = "intrinsic"
    EXTRINSIC = "extrinsic"


# ─────────────────────────────────────────────────────────────────────────────
# Base Executor Classes
# ─────────────────────────────────────────────────────────────────────────────

class RuntimeExecutor(ABC):
    """Abstract base class for runtime executors.
    
    Each executor manages a specific runtime environment (Python, JavaScript, etc.)
    and can operate in either intrinsic or extrinsic boundary mode.
    """
    
    # Default boundary type for this runtime
    boundary_type: BoundaryType = BoundaryType.INTRINSIC
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def execute(self, concrete_impl: Dict[str, Any], target: MCard, context: Dict[str, Any]) -> Any:
        """Execute the operation in the runtime environment."""
        pass
    
    @abstractmethod
    def validate_environment(self) -> bool:
        """Check if runtime environment is available."""
        pass
    
    def get_boundary_type(self) -> BoundaryType:
        """Get the boundary type for this runtime.
        
        Override in subclasses to provide dynamic boundary determination.
        """
        return self.boundary_type
    
    def is_intrinsic(self) -> bool:
        """Check if this runtime operates within the same process."""
        return self.get_boundary_type() == BoundaryType.INTRINSIC
    
    def is_extrinsic(self) -> bool:
        """Check if this runtime operates in a separate process."""
        return self.get_boundary_type() == BoundaryType.EXTRINSIC
    
    def get_runtime_status(self) -> Dict[str, Any]:
        """Get detailed status information about this runtime."""
        return {
            'available': self.validate_environment(),
            'version': None,
            'command': self.__class__.__name__.replace('Runtime', '').lower(),
            'details': ''
        }


class SubprocessRuntime(RuntimeExecutor):
    """
    Base class for runtimes that execute via subprocess.
    Reduces duplication across Rust/C/Lean/R/Julia.
    
    Note: Subprocess runtimes are EXTRINSIC - they run in separate processes.
    """
    
    # Subprocess runtimes are extrinsic by default
    boundary_type: BoundaryType = BoundaryType.EXTRINSIC
    
    runtime_name: str = ""
    command: Optional[str] = None
    version_flag: str = "--version"
    timeout: int = DEFAULT_TIMEOUT
    
    def _run_subprocess(
        self,
        cmd: List[str],
        target: MCard,
        context: Dict,
        timeout: Optional[int] = None
    ) -> str:
        """Execute subprocess and return output or error string."""
        try:
            result = subprocess.run(
                cmd,
                input=target.get_content(),
                capture_output=True,
                timeout=timeout or self.timeout
            )
            if result.returncode != 0:
                return f"Error: {self.runtime_name} execution failed: {result.stderr.decode()}"
            return result.stdout.decode('utf-8')
        except subprocess.TimeoutExpired:
            return f"Error: {self.runtime_name} execution timed out"
        except Exception as e:
            return f"Error executing {self.runtime_name}: {e}"
    
    def _check_command(self, cmd: Any, flag: str, timeout: int = 10) -> bool:
        """Check if a command is available."""
        try:
            if isinstance(cmd, list):
                args = cmd + [flag]
            else:
                args = [cmd, flag]
                
            result = subprocess.run(args, capture_output=True, timeout=timeout)
            if result.returncode != 0:
                self.logger.debug(f"Command check failed for {args}: {result.stderr.decode()}")
                return False
            return True
        except Exception as e:
            self.logger.debug(f"Exception checking command {cmd}: {e}")
            return False
    
    def validate_environment(self) -> bool:
        if not self.command:
            return True  # No command needed (e.g., compiled binaries)
        return self._check_command(self.command, self.version_flag)
