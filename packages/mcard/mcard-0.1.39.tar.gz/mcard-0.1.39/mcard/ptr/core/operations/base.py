"""
Base classes and protocols for operations.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, Protocol, runtime_checkable

from mcard import MCard


@runtime_checkable
class Operation(Protocol):
    """Protocol for operation callables.
    
    All operations must be callable with signature:
        (impl: Dict, target: MCard, ctx: Dict) -> Any
    """
    
    def __call__(self, impl: Dict[str, Any], target: MCard, ctx: Dict[str, Any]) -> Any:
        """Execute the operation.
        
        Args:
            impl: Concrete implementation configuration from CLM
            target: The target MCard
            ctx: Execution context
            
        Returns:
            Operation result (type depends on operation)
        """
        ...


class OperationRegistry:
    """Registry for operation handlers.
    
    Provides a centralized place to register and retrieve operations.
    Supports dynamic registration for extending with custom operations.
    """
    
    def __init__(self):
        self._operations: Dict[str, Callable] = {}
    
    def register(self, name: str, handler: Callable) -> None:
        """Register an operation handler."""
        self._operations[name] = handler
    
    def register_many(self, operations: Dict[str, Callable]) -> None:
        """Register multiple operation handlers at once."""
        self._operations.update(operations)
    
    def get(self, name: str) -> Optional[Callable]:
        """Get an operation handler by name."""
        return self._operations.get(name)
    
    def has(self, name: str) -> bool:
        """Check if an operation is registered."""
        return name in self._operations
    
    def list_operations(self) -> list:
        """List all registered operation names."""
        return list(self._operations.keys())


class ExampleRunnerMixin:
    """Mixin providing generic example running capability.
    
    Reduces code duplication in operations that need to run
    batches of examples and aggregate results.
    """
    
    @staticmethod
    def run_examples(
        examples: list,
        executor: Callable[[dict], Dict[str, Any]],
        validator: Callable[[Dict[str, Any], Dict[str, Any]], bool]
    ) -> Dict[str, Any]:
        """Run examples through an executor and validate results.
        
        Args:
            examples: List of example dicts with 'input' and optionally 'expected_output'
            executor: Function that takes input_data and returns result dict
            validator: Function that takes (result, expected) and returns bool
            
        Returns:
            Aggregated result with 'success' and 'results' keys
        """
        results = []
        for example in examples:
            input_data = example.get('input', example)
            
            # Execute
            try:
                result = executor(input_data)
            except Exception as e:
                result = {'success': False, 'error': str(e)}
            
            result['example_name'] = example.get('name', 'unnamed')
            
            # Validate against expected if provided
            expected = example.get('expected_output', {})
            if expected:
                result['passed'] = validator(result, expected)
            else:
                result['passed'] = result.get('success', False)
            
            results.append(result)
        
        all_passed = all(r.get('passed', False) for r in results)
        return {'success': all_passed, 'results': results}
