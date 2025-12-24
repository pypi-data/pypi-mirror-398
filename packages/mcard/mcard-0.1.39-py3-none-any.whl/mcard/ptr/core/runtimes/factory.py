"""
Runtime Factory for creating runtime executors.

This module provides the factory pattern for creating and caching
runtime executors based on configuration.
"""

import logging
from typing import Any, Dict, Optional

from .base import RuntimeType, RuntimeExecutor


class RuntimeFactory:
    """Factory for creating runtime executors based on configuration."""
    
    _executors: Dict[RuntimeType, RuntimeExecutor] = {}
    _availability_cache: Dict[RuntimeType, bool] = {}  # Cache for availability checks
    _detailed_status_cache: Optional[Dict[str, Dict[str, Any]]] = None
    
    # Executor map will be populated lazily to avoid circular imports
    _EXECUTOR_MAP: Dict[RuntimeType, type] = None
    
    @classmethod
    def _get_executor_map(cls):
        """Lazily initialize executor map to avoid circular imports."""
        if cls._EXECUTOR_MAP is None:
            # Import here to avoid circular dependencies
            from .python import PythonRuntime
            from .javascript import JavaScriptRuntime
            from .binary import RustRuntime, CRuntime
            from .script import LeanRuntime, RRuntime, JuliaRuntime
            from .lambda_calc import LambdaRuntimeExecutor
            
            cls._EXECUTOR_MAP = {
                RuntimeType.PYTHON: PythonRuntime,
                RuntimeType.JAVASCRIPT: JavaScriptRuntime,
                RuntimeType.RUST: RustRuntime,
                RuntimeType.C: CRuntime,
                RuntimeType.WASM: RustRuntime,
                RuntimeType.LEAN: LeanRuntime,
                RuntimeType.R: RRuntime,
                RuntimeType.JULIA: JuliaRuntime,
                RuntimeType.LAMBDA: LambdaRuntimeExecutor,
            }
        return cls._EXECUTOR_MAP
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear cached availability data. Useful for testing or env changes."""
        cls._availability_cache.clear()
        cls._detailed_status_cache = None
        cls._executors.clear()
    
    @classmethod
    def get_executor(cls, runtime_type: str) -> Optional[RuntimeExecutor]:
        """Get or create a runtime executor for the specified type."""
        # Handle LLM runtime specially (dynamic import to avoid circular dependency)
        if runtime_type.lower() == 'llm':
            return cls._get_llm_executor()
        
        # Handle Lambda runtime specially (needs CardCollection)
        if runtime_type.lower() == 'lambda':
            return cls._get_lambda_executor()
        
        # Handle Network runtime specially (dynamic import)
        if runtime_type.lower() == 'network':
            return cls._get_network_executor()
            
        # User defined aliases
        if runtime_type.lower() == 'node':
            runtime_type = 'javascript'
        
        try:
            rt_type = RuntimeType(runtime_type.lower())
        except ValueError:
            logging.error(f"Unsupported runtime type: {runtime_type}")
            return None
        
        if rt_type not in cls._executors:
            executor = cls._create_executor(rt_type)
            if executor and cls._is_available(rt_type, executor):
                cls._executors[rt_type] = executor
            else:
                logging.warning(f"Runtime {runtime_type} not available or invalid")
                return None
        
        return cls._executors.get(rt_type)
    
    @classmethod
    def _is_available(cls, rt_type: RuntimeType, executor: RuntimeExecutor) -> bool:
        """Check if runtime is available, using cache."""
        if rt_type not in cls._availability_cache:
            cls._availability_cache[rt_type] = executor.validate_environment()
        return cls._availability_cache[rt_type]
    
    @classmethod
    def _get_llm_executor(cls) -> Optional[RuntimeExecutor]:
        """Get LLM executor with dynamic import."""
        if RuntimeType.LLM in cls._executors:
            return cls._executors[RuntimeType.LLM]
        
        try:
            from mcard.ptr.core.llm import LLMRuntime
            executor = LLMRuntime()
            if executor.validate_environment():
                cls._executors[RuntimeType.LLM] = executor
                return executor
            else:
                logging.warning("LLM runtime not available (Ollama not running?)")
                return None
        except ImportError as e:
            logging.error(f"Failed to import LLM runtime: {e}")
            return None
    
    @classmethod
    def _get_lambda_executor(cls) -> Optional[RuntimeExecutor]:
        """Get Lambda Calculus executor with dynamic import."""
        if RuntimeType.LAMBDA in cls._executors:
            return cls._executors[RuntimeType.LAMBDA]
        
        try:
            from mcard.ptr.lambda_calc import LambdaRuntime
            from mcard.model.card_collection import CardCollection
            from .lambda_calc import LambdaRuntimeExecutor
            
            # Create an in-memory collection for Lambda terms
            collection = CardCollection(db_path=":memory:")
            executor = LambdaRuntimeExecutor(collection)
            cls._executors[RuntimeType.LAMBDA] = executor
            return executor
        except ImportError as e:
            logging.error(f"Failed to import Lambda runtime: {e}")
            return None
    
    @classmethod
    def _get_network_executor(cls) -> Optional[RuntimeExecutor]:
        """Get Network IO executor with dynamic import."""
        if RuntimeType.NETWORK in cls._executors:
            return cls._executors[RuntimeType.NETWORK]
        
        try:
            from mcard.ptr.network import NetworkRuntime
            from mcard.model.card_collection import CardCollection
            
            # Create an in-memory collection for network operations
            collection = CardCollection(db_path=":memory:")
            executor = NetworkRuntime(collection)
            cls._executors[RuntimeType.NETWORK] = executor
            return executor
        except ImportError as e:
            logging.error(f"Failed to import Network runtime: {e}")
            return None
    
    @classmethod
    def _create_executor(cls, runtime_type: RuntimeType) -> Optional[RuntimeExecutor]:
        """Create a new runtime executor."""
        # Handle LLM specially (dynamic import)
        if runtime_type == RuntimeType.LLM:
            try:
                from mcard.ptr.core.llm import LLMRuntime
                return LLMRuntime()
            except ImportError:
                return None
        
        executor_map = cls._get_executor_map()
        executor_class = executor_map.get(runtime_type)
        return executor_class() if executor_class else None
    
    @classmethod
    def list_available_runtimes(cls) -> Dict[str, bool]:
        """List all runtime types and their availability (cached)."""
        result = {}
        for rt in RuntimeType:
            if rt not in cls._availability_cache:
                executor = cls._create_executor(rt)
                cls._availability_cache[rt] = executor.validate_environment() if executor else False
            result[rt.value] = cls._availability_cache[rt]
        return result
    
    @classmethod
    def get_detailed_status(cls) -> Dict[str, Dict[str, Any]]:
        """Get detailed status information for all runtimes (cached)."""
        if cls._detailed_status_cache is not None:
            return cls._detailed_status_cache
        
        status = {}
        for rt in RuntimeType:
            executor = cls._create_executor(rt)
            status[rt.value] = (executor.get_runtime_status() if executor else {
                'available': False, 'version': None, 'command': rt.value,
                'details': 'Runtime executor not implemented'
            })
        cls._detailed_status_cache = status
        return status
    
    @classmethod
    def at_least_one_available(cls) -> bool:
        """Check if at least one runtime is available."""
        return any(cls.list_available_runtimes().values())
    
    @classmethod
    def print_status(cls, verbose: bool = False) -> None:
        """Print runtime status to console."""
        print("\n=== Polyglot Runtime Status ===")
        for name, info in cls.get_detailed_status().items():
            if info['available']:
                ver = f" {info['version']}" if info['version'] else ""
                detail = f": {info['details']}" if verbose and info['details'] else ""
                print(f"✓ {name.capitalize()}{ver}{detail}")
            else:
                print(f"✗ {name.capitalize()} not found")
        
        available = sum(1 for i in cls.get_detailed_status().values() if i['available'])
        print(f"{'=' * 31}\nAvailable: {available}/{len(RuntimeType)} runtimes")
