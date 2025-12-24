"""
Lambda Calculus runtime executor.

Executes λ-calculus operations (α-β-η conversions) on MCard-stored terms.
"""

from typing import Any

from mcard import MCard

from .base import RuntimeExecutor


class LambdaRuntimeExecutor(RuntimeExecutor):
    """Lambda Calculus runtime executor.

    Executes λ-calculus operations (α-β-η conversions) on MCard-stored terms.
    """

    def __init__(self, collection=None):
        super().__init__()
        self.collection = collection
        self._lambda_runtime = None

    def _get_runtime(self):
        """Lazy initialization of LambdaRuntime."""
        if self._lambda_runtime is None:
            from mcard.model.card_collection import CardCollection
            from mcard.ptr.lambda_calc import LambdaRuntime

            if self.collection is None:
                self.collection = CardCollection(db_path=":memory:")
            self._lambda_runtime = LambdaRuntime(self.collection)
        return self._lambda_runtime

    def execute(self, impl: dict[str, Any], target: MCard, ctx: dict[str, Any]) -> Any:
        """Execute Lambda Calculus operation."""
        runtime = self._get_runtime()

        # Build context from concrete implementation and context
        # Prioritize ctx override, then 'process', then 'action', then 'operation'
        operation = ctx.get('operation',
                           impl.get('process',
                                   impl.get('action',
                                           impl.get('operation', 'normalize'))))
        strategy = ctx.get('strategy', impl.get('strategy', 'normal'))
        max_steps = ctx.get('max_steps', ctx.get('maxSteps', impl.get('max_steps', impl.get('maxSteps', 100))))

        # Get expression from context or target
        expression = ctx.get('expression')
        if not expression:
            # Try to get from balanced input arguments
            balanced = ctx.get('balanced', {})
            input_args = balanced.get('input_arguments', {})
            expression = input_args.get('expression') or input_args.get('numeral')

        if not expression or expression == 'dummy_target':
            # Check if target content looks like a Lambda expression
            target_content = target.get_content().decode('utf-8', errors='ignore')
            if target_content and ('λ' in target_content or '\\' in target_content):
                expression = target_content
            elif operation in ('check-readiness', 'num-add', 'num-sub', 'num-mul', 'num-div', 'http-request'):
                expression = 'builtin' # Placeholder
            else:
                return "Error: No Lambda expression provided"

        # Execute through LambdaRuntime
        # Create a full context by merging ctx and any other needed fields
        full_ctx = ctx.copy()
        full_ctx['expression'] = expression

        # Get io_effects from concrete implementation config
        io_effects = impl.get('io_effects')

        result = runtime.execute(
            expression,
            full_ctx,
            {
                'operation': operation,
                'strategy': strategy,
                'max_steps': max_steps,
                'io_effects': io_effects
            },
            ''
        )

        if result.success:
            # Return appropriate result based on operation
            if result.pretty_print:
                return result.pretty_print
            elif result.is_closed is not None:
                return result.is_closed
            elif result.free_variables is not None:
                return result.free_variables
            else:
                return result.term_hash
        else:
            return f"Error: {result.error}"

    def validate_environment(self) -> bool:
        """Lambda runtime is always available (pure Python)."""
        return True

    def get_runtime_status(self) -> dict[str, Any]:
        return {
            'available': True,
            'version': '1.0.0',
            'command': 'lambda',
            'details': 'Lambda Calculus α-β-η converter'
        }
