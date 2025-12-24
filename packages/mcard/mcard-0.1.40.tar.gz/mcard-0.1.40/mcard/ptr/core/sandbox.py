"""
Sandbox execution environment for PCards with multi-language runtime support.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from mcard import MCard
from .runtime import RuntimeFactory
from .monads import IO, Either, Left, Right

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_RUNTIME = 'python'

# Error message patterns for system errors (these should raise exceptions)
SYSTEM_ERROR_PATTERNS = (
    "Failed to parse PCard",
    "Sandbox execution failed",
)

# Fallback resolution order
FALLBACK_SOURCES = ('mcard', 'file', 'url')


# ─────────────────────────────────────────────────────────────────────────────
# Code Resolution Strategies
# ─────────────────────────────────────────────────────────────────────────────

class CodeResolver:
    """Resolves code from multiple sources with fallback chain."""
    
    def __init__(self, collection=None, logger=None):
        self.collection = collection
        self.logger = logger or logging.getLogger(__name__)
    
    def resolve(self, concrete_impl: Dict, context: Dict) -> Either[str, Optional[str]]:
        """
        Resolve code from available sources in priority order.
        
        Returns:
            Right(code) on success, Left(error) on failure
        """
        # Already have code
        if concrete_impl.get('code'):
            return Right(concrete_impl['code'])
        
        # No code hash means no content-addressed lookup needed
        code_hash = concrete_impl.get('code_hash')
        
        # If no code source is specified, return None (success, no code needed)
        if not any([code_hash, concrete_impl.get('code_file'), concrete_impl.get('fallback_file'), concrete_impl.get('fallback_url')]):
             return Right(None)
             
        # Try resolution sources in order
        resolvers = [
            ('mcard', lambda: self._from_mcard(code_hash) if code_hash else None),
            ('file', lambda: self._from_file(concrete_impl.get('code_file') or concrete_impl.get('fallback_file'), context, code_hash or 'unknown')),
            ('url', lambda: self._from_url(concrete_impl.get('fallback_url'), code_hash or 'unknown')),
        ]
        
        for source_name, resolver in resolvers:
            result = resolver()
            if result is not None:
                return Right(result)
        
        return Left(f"Error: Code resolution failed. MCard {code_hash} not found, and fallbacks failed.")
    
    def _from_mcard(self, code_hash: str) -> Optional[str]:
        """Try to resolve code from MCard collection."""
        if not self.collection:
            return None
        
        code_card = self.collection.get(code_hash)
        if code_card:
            self.logger.info(f"Resolved code from MCard: {code_hash}")
            return code_card.get_content().decode('utf-8')
        return None
    
    def _from_file(self, fallback_file: Optional[str], context: Dict, code_hash: str) -> Optional[str]:
        """Try to resolve code from fallback file."""
        if not fallback_file:
            return None
        
        try:
            path = self._resolve_file_path(fallback_file, context)
            if path and path.exists():
                self.logger.warning(f"MCard not found for hash {code_hash}, loaded from fallback file: {fallback_file}")
                return path.read_text()
            self.logger.warning(f"Fallback file not found: {path}")
        except Exception as e:
            self.logger.error(f"Failed to load fallback file {fallback_file}: {e}")
        return None
    
    def _from_url(self, fallback_url: Optional[str], code_hash: str) -> Optional[str]:
        """Try to resolve code from fallback URL."""
        if not fallback_url:
            return None
        
        try:
            import urllib.request
            with urllib.request.urlopen(fallback_url) as response:
                status = getattr(response, 'status', None) or getattr(response, 'code', 200)
                if status == 200:
                    self.logger.warning(f"Loaded code from fallback URL: {fallback_url}")
                    return response.read().decode('utf-8')
                self.logger.error(f"Failed to fetch fallback URL {fallback_url}: Status {status}")
        except Exception as e:
            self.logger.error(f"Failed to fetch fallback URL {fallback_url}: {e}")
        return None
    
    @staticmethod
    def _resolve_file_path(file_path: str, context: Dict) -> Optional[Path]:
        """Resolve a file path, handling relative paths."""
        path = Path(file_path)
        if path.is_absolute():
            return path
        
        # Try pcard_dir first, then cwd
        pcard_dir = context.get('pcard_dir') if context else None
        if pcard_dir:
            candidate = Path(pcard_dir) / path
            if candidate.exists():
                return candidate
        
        return Path.cwd() / path


# ─────────────────────────────────────────────────────────────────────────────
# Sandbox Executor
# ─────────────────────────────────────────────────────────────────────────────

class SandboxExecutor:
    """
    Executes PCard logic in a sandboxed environment with multi-language support.
    
    The sandbox dynamically selects the appropriate runtime (Python, JavaScript,
    Rust, C, etc.) based on the Concrete Implementation specification in the PCard.
    
    Production deployments should use:
    - WebAssembly (WASM) for true sandboxing
    - Container isolation (Docker/Kubernetes)
    - Resource limits and timeout enforcement
    """

    def __init__(self, collection=None):
        self.logger = logging.getLogger(__name__)
        self.collection = collection
        self._code_resolver = CodeResolver(collection, self.logger)

    def execute(self, pcard: MCard, target: MCard, context: Dict[str, Any]) -> Any:
        """
        Execute PCard logic using the specified runtime.
        
        The runtime is determined from the Concrete Implementation's 'runtime' field.
        Defaults to 'python' if not specified.
        """
        result_either = self.execute_monad(pcard, target, context).unsafe_run()
        
        if result_either.is_left():
            error_msg = result_either.value
            if self._is_system_error(error_msg):
                raise RuntimeError(error_msg)
            return error_msg
        return result_either.value

    def execute_monad(self, pcard: MCard, target: MCard, context: Dict[str, Any]) -> IO[Either[str, Any]]:
        """Monadic execution pipeline returning IO[Either[Error, Result]]."""
        
        def run() -> Either[str, Any]:
            try:
                return self._pipeline(pcard, target, context)
            except Exception as e:
                return Left(f"Sandbox execution failed: {e}")
        
        return IO(run)

    def _pipeline(self, pcard: MCard, target: MCard, context: Dict) -> Either[str, Any]:
        """Execute the main processing pipeline."""
        # 1. Parse PCard
        pcard_data = self._parse_pcard(pcard)
        if pcard_data.is_left():
            return pcard_data
        
        concrete_impl = pcard_data.value.get('concrete', {})
        
        # 2. Resolve Code
        code_result = self._code_resolver.resolve(concrete_impl, context)
        if code_result.is_left():
            return code_result
        
        if code_result.value:
            concrete_impl['code'] = code_result.value
        
        # 3. Get Executor
        runtime_type = concrete_impl.get('runtime', DEFAULT_RUNTIME)
        self.logger.info(f"Executing PCard with runtime: {runtime_type}")
        
        executor = RuntimeFactory.get_executor(runtime_type)
        if not executor:
            return Left(f"Error: Runtime '{runtime_type}' is not available or not supported")
        
        # 4. Execute
        return self._execute_runtime(executor, concrete_impl, target, context)

    def _parse_pcard(self, pcard: MCard) -> Either[str, Dict]:
        """Parse PCard YAML content."""
        try:
            import yaml
            return Right(yaml.safe_load(pcard.get_content().decode('utf-8')))
        except Exception as e:
            return Left(f"Failed to parse PCard: {e}")

    def _execute_runtime(self, executor: Any, concrete_impl: Dict, target: MCard, context: Dict) -> Either[str, Any]:
        """Execute using the selected runtime."""
        try:
            result = executor.execute(concrete_impl, target, context)
            if isinstance(result, str) and result.startswith("Error:"):
                return Left(result)
            return Right(result)
        except Exception as e:
            return Left(f"Runtime execution failed: {e}")

    @staticmethod
    def _is_system_error(error_msg: str) -> bool:
        """Check if error message indicates a system-level error."""
        return any(pattern in error_msg for pattern in SYSTEM_ERROR_PATTERNS)

    def list_available_runtimes(self) -> Dict[str, bool]:
        """Get list of available runtimes on this system."""
        return RuntimeFactory.list_available_runtimes()
