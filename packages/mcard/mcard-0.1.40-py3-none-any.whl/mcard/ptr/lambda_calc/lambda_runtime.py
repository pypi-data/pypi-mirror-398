"""
Lambda Runtime - PTR interface for Lambda Calculus

Provides a unified runtime interface for Lambda Calculus operations,
integrating the parser and all conversion modules.

This module provides Python parity with mcard-js/src/ptr/lambda/LambdaRuntime.ts
"""

from dataclasses import dataclass
from typing import Any, Literal, Optional

from mcard.model.card_collection import CardCollection
from mcard.ptr.lambda_calc.alpha_conversion import alpha_equivalent, alpha_normalize
from mcard.ptr.lambda_calc.beta_reduction import (
    ReductionStrategy,
    beta_reduce,
    normalize,
)
from mcard.ptr.lambda_calc.eta_conversion import eta_expand, eta_reduce
from mcard.ptr.lambda_calc.free_variables import free_variables, is_closed
from mcard.ptr.lambda_calc.io_effects import create_io_handler
from mcard.ptr.lambda_calc.lambda_term import (
    AbsTerm,
    AppTerm,
    VarTerm,
    load_term,
    mk_abs,
    mk_app,
    mk_var,
    pretty_print_deep,
    store_term,
)

# ─────────────────────────────────────────────────────────────────────────────
# Parser
# ─────────────────────────────────────────────────────────────────────────────

class ParseError(Exception):
    """Error during Lambda expression parsing"""
    pass


def parse_lambda_expression(collection: CardCollection, expr: str) -> str:
    """
    Parse a Lambda expression string and store terms in collection.

    Syntax:
      <term> ::= <var> | <abs> | <app> | "(" <term> ")"
      <var>  ::= [a-zA-Z][a-zA-Z0-9']*
      <abs>  ::= ("λ" | "\\") <var> "." <term>
      <app>  ::= <term> <term>

    Returns the hash of the parsed term.
    """
    parser = LambdaParser(collection, expr)
    return parser.parse()


class LambdaParser:
    """Recursive descent parser for Lambda expressions"""

    def __init__(self, collection: CardCollection, input_str: str):
        self.collection = collection
        self.input = input_str.strip()
        self.pos = 0

    def parse(self) -> str:
        """Parse the entire input and return term hash"""
        result = self._parse_term()
        self._skip_whitespace()
        if self.pos < len(self.input):
            raise ParseError(f"Unexpected character at position {self.pos}: '{self.input[self.pos]}'")
        return result

    def _skip_whitespace(self):
        """Skip whitespace characters"""
        while self.pos < len(self.input) and self.input[self.pos] in ' \t\n\r':
            self.pos += 1

    def _peek(self) -> Optional[str]:
        """Look at current character without consuming"""
        self._skip_whitespace()
        if self.pos >= len(self.input):
            return None
        return self.input[self.pos]

    def _consume(self, char: str):
        """Consume expected character"""
        self._skip_whitespace()
        if self.pos >= len(self.input):
            raise ParseError(f"Expected '{char}' but reached end of input")
        if self.input[self.pos] != char:
            raise ParseError(f"Expected '{char}' but found '{self.input[self.pos]}' at position {self.pos}")
        self.pos += 1

    def _parse_term(self) -> str:
        """Parse a Lambda term (handles application as left-associative)"""
        atoms = []

        while True:
            atom = self._parse_atom()
            if atom is None:
                break
            atoms.append(atom)

        if not atoms:
            raise ParseError(f"Expected term at position {self.pos}")

        # Build left-associative application
        result = atoms[0]
        for i in range(1, len(atoms)):
            result = store_term(self.collection, mk_app(result, atoms[i]))

        return result

    def _parse_atom(self) -> Optional[str]:
        """Parse an atomic term (variable, abstraction, or parenthesized)"""
        self._skip_whitespace()

        if self.pos >= len(self.input):
            return None

        c = self.input[self.pos]

        # Lambda/backslash - abstraction
        if c == 'λ' or c == '\\':
            return self._parse_abstraction()

        # Open paren - grouped term
        if c == '(':
            return self._parse_grouped()

        # Variable
        if c.isalpha():
            return self._parse_variable()

        return None

    def _parse_variable(self) -> str:
        """Parse a variable name"""
        self._skip_whitespace()
        start = self.pos

        # First character must be letter
        if self.pos >= len(self.input) or not self.input[self.pos].isalpha():
            raise ParseError(f"Expected variable at position {self.pos}")

        # Read variable name
        while (self.pos < len(self.input) and
               (self.input[self.pos].isalnum() or self.input[self.pos] in ("'", "_"))):
            self.pos += 1

        name = self.input[start:self.pos]
        return store_term(self.collection, mk_var(name))

    def _parse_abstraction(self) -> str:
        """Parse an abstraction: λx.M or \\x.M"""
        self._skip_whitespace()

        # Consume lambda symbol
        if self.input[self.pos] == 'λ':
            self.pos += 1
        elif self.input[self.pos] == '\\':
            self.pos += 1
        else:
            raise ParseError(f"Expected λ or \\ at position {self.pos}")

        self._skip_whitespace()

        # Parse parameter
        start = self.pos
        while (self.pos < len(self.input) and
               (self.input[self.pos].isalnum() or self.input[self.pos] in ("'", "_"))):
            self.pos += 1

        if self.pos == start:
            raise ParseError(f"Expected parameter name at position {self.pos}")

        param = self.input[start:self.pos]

        # Consume dot
        self._skip_whitespace()
        self._consume('.')

        # Parse body
        body = self._parse_term()

        return store_term(self.collection, mk_abs(param, body))

    def _parse_grouped(self) -> str:
        """Parse a parenthesized term: (M)"""
        self._consume('(')
        term = self._parse_term()
        self._consume(')')
        return term


# ─────────────────────────────────────────────────────────────────────────────
# Lambda Runtime
# ─────────────────────────────────────────────────────────────────────────────

LambdaOperation = Literal[
    'parse',
    'normalize',
    'normalize-applicative',
    'normalize-lazy',
    'beta-reduce',
    'alpha-equiv',
    'alpha-normalize',
    'eta-reduce',
    'eta-expand',
    'free-vars',
    'is-closed',
    'pretty-print',
    'check-readiness',
    'num-add',
    'num-sub',
    'num-mul',
    'num-div',
    'http-request',
    'church-to-int'
]


@dataclass
class LambdaConfig:
    """Configuration for Lambda runtime operations"""
    operation: LambdaOperation = 'normalize'
    strategy: ReductionStrategy = 'normal'
    max_steps: int = 100
    io_effects: Optional[dict[str, Any]] = None


@dataclass
class LambdaRuntimeResult:
    """Result from Lambda runtime execution"""
    success: bool
    term_hash: Optional[str] = None
    pretty_print: Optional[str] = None
    free_variables: Optional[list[str]] = None
    is_closed: Optional[bool] = None
    steps: Optional[int] = None
    alpha_equivalent: Optional[bool] = None
    eta_equivalent: Optional[bool] = None
    error: Optional[str] = None


class LambdaRuntime:
    """
    Lambda Calculus runtime for PTR.

    Provides α-β-η conversions on MCard-stored Lambda terms.
    """

    def __init__(self, collection: CardCollection):
        self.collection = collection

    def execute(
        self,
        code_or_hash: str,
        context: dict[str, Any],
        config: dict[str, Any],
        chapter_dir: str = ''
    ) -> LambdaRuntimeResult:
        """
        Execute a Lambda operation.

        Args:
            code_or_hash: Either a Lambda expression string or a term hash
            context: Additional context (may contain 'expression', 'other_hash')
            config: Operation configuration
            chapter_dir: Working directory (unused)

        Returns:
            LambdaRuntimeResult with operation output
        """
        try:
            operation = config.get('operation', 'normalize')
            strategy = config.get('strategy', 'normal')
            max_steps = config.get('max_steps', config.get('maxSteps', 100))

            # Parse expression if provided in context
            if context.get('expression'):
                term_hash = parse_lambda_expression(self.collection, context['expression'])
            elif code_or_hash and len(code_or_hash) == 64:
                # Looks like a hash
                term_hash = code_or_hash
            elif code_or_hash and code_or_hash.strip():
                # Parse as expression
                term_hash = parse_lambda_expression(self.collection, code_or_hash)
            else:
                return LambdaRuntimeResult(success=False, error="No expression or hash provided")

            # Execute operation
            if operation == 'parse':
                return self._parse(context)

            elif operation == 'normalize':
                return self._normalize(term_hash, strategy, max_steps, config)

            elif operation == 'normalize-applicative':
                return self._normalize(term_hash, 'applicative', max_steps, config)

            elif operation == 'normalize-lazy':
                return self._normalize(term_hash, 'lazy', max_steps, config)

            elif operation == 'beta-reduce':
                return self._beta_reduce(term_hash)

            elif operation == 'alpha-equiv':
                other_hash = context.get('other_hash')
                if not other_hash:
                    return LambdaRuntimeResult(success=False, error="alpha-equiv requires 'other_hash' in context")
                return self._alpha_equiv(term_hash, other_hash)

            elif operation == 'alpha-normalize':
                return self._alpha_normalize(term_hash)

            elif operation == 'eta-reduce':
                return self._eta_reduce(term_hash)

            elif operation == 'eta-expand':
                return self._eta_expand(term_hash)

            elif operation == 'free-vars':
                return self._free_vars(term_hash)

            elif operation == 'is-closed':
                return self._is_closed(term_hash)

            elif operation == 'pretty-print':
                return self._pretty_print(term_hash)

            elif operation == 'check-readiness':
                return self._check_readiness(context)

            elif operation.startswith('num-'):
                return self._numeric_op(operation, context)

            elif operation == 'http-request':
                return self._http_request(context)

            elif operation == 'church-to-int':
                return self._church_to_int(term_hash)

            else:
                return LambdaRuntimeResult(success=False, error=f"Unknown operation: {operation}")

        except ParseError as e:
            return LambdaRuntimeResult(success=False, error=f"Parse error: {str(e)}")
        except Exception as e:
            return LambdaRuntimeResult(success=False, error=str(e))

    def _parse(self, context: dict[str, Any]) -> LambdaRuntimeResult:
        """Parse a Lambda expression"""
        expr = context.get('expression', '')
        if not expr:
            return LambdaRuntimeResult(success=False, error="No expression to parse")

        term_hash = parse_lambda_expression(self.collection, expr)
        pretty = pretty_print_deep(self.collection, term_hash)

        return LambdaRuntimeResult(
            success=True,
            term_hash=term_hash,
            pretty_print=pretty
        )

    def _normalize(
        self,
        term_hash: str,
        strategy: str,
        max_steps: int,
        config: dict[str, Any]
    ) -> LambdaRuntimeResult:
        """Normalize a term with optional IO effects"""
        # Create IO effects handler from config
        io_handler = create_io_handler(config)

        # IO callback for step events
        def on_step(step: int, hash: str) -> None:
            if io_handler.is_enabled():
                pretty = pretty_print_deep(self.collection, hash)
                io_handler.emit_step(step, hash, pretty)

        result = normalize(
            self.collection,
            term_hash,
            strategy,
            max_steps,
            on_step=on_step if io_handler.is_enabled() else None
        )

        if result is None:
            if io_handler.is_enabled():
                io_handler.emit_error("Normalization failed or diverged", 0)
            return LambdaRuntimeResult(success=False, error="Normalization failed or diverged")

        pretty = pretty_print_deep(self.collection, result.normal_form)

        # IO Effect: emit completion
        if io_handler.is_enabled():
            io_handler.emit_complete(
                result.normal_form,
                pretty,
                result.steps,
                result.reduction_path
            )

        return LambdaRuntimeResult(
            success=True,
            term_hash=result.normal_form,
            pretty_print=pretty,
            steps=result.steps
        )

    def _beta_reduce(self, term_hash: str) -> LambdaRuntimeResult:
        """Single beta reduction step"""
        result = beta_reduce(self.collection, term_hash)

        if result is None:
            return LambdaRuntimeResult(success=False, error="Not a redex")

        pretty = pretty_print_deep(self.collection, result)

        return LambdaRuntimeResult(
            success=True,
            term_hash=result,
            pretty_print=pretty
        )

    def _alpha_equiv(self, hash1: str, hash2: str) -> LambdaRuntimeResult:
        """Check alpha equivalence"""
        equiv = alpha_equivalent(self.collection, hash1, hash2)

        if equiv is None:
            return LambdaRuntimeResult(success=False, error="Terms not found")

        return LambdaRuntimeResult(
            success=True,
            alpha_equivalent=equiv
        )

    def _alpha_normalize(self, term_hash: str) -> LambdaRuntimeResult:
        """Normalize bound variable names"""
        result = alpha_normalize(self.collection, term_hash)

        if result is None:
            return LambdaRuntimeResult(success=False, error="Alpha normalization failed")

        pretty = pretty_print_deep(self.collection, result)

        return LambdaRuntimeResult(
            success=True,
            term_hash=result,
            pretty_print=pretty
        )

    def _eta_reduce(self, term_hash: str) -> LambdaRuntimeResult:
        """Eta reduce a term"""
        result = eta_reduce(self.collection, term_hash)

        if result is None:
            return LambdaRuntimeResult(success=False, error="Eta reduction failed")

        pretty = pretty_print_deep(self.collection, result)

        return LambdaRuntimeResult(
            success=True,
            term_hash=result,
            pretty_print=pretty
        )

    def _eta_expand(self, term_hash: str) -> LambdaRuntimeResult:
        """Eta expand a term"""
        result = eta_expand(self.collection, term_hash)

        if result is None:
            return LambdaRuntimeResult(success=False, error="Eta expansion failed")

        pretty = pretty_print_deep(self.collection, result)

        return LambdaRuntimeResult(
            success=True,
            term_hash=result,
            pretty_print=pretty
        )

    def _free_vars(self, term_hash: str) -> LambdaRuntimeResult:
        """Get free variables"""
        fv = free_variables(self.collection, term_hash)

        if fv is None:
            return LambdaRuntimeResult(success=False, error="Term not found")

        return LambdaRuntimeResult(
            success=True,
            term_hash=term_hash,
            free_variables=sorted(fv)
        )

    def _is_closed(self, term_hash: str) -> LambdaRuntimeResult:
        """Check if term is closed"""
        closed = is_closed(self.collection, term_hash)

        if closed is None:
            return LambdaRuntimeResult(success=False, error="Term not found")

        pretty = pretty_print_deep(self.collection, term_hash)

        return LambdaRuntimeResult(
            success=True,
            term_hash=term_hash,
            pretty_print=pretty,
            is_closed=closed
        )

    def _pretty_print(self, term_hash: str) -> LambdaRuntimeResult:
        """Pretty print a term"""
        pretty = pretty_print_deep(self.collection, term_hash)

        return LambdaRuntimeResult(
            success=True,
            term_hash=term_hash,
            pretty_print=pretty
        )

    def _check_readiness(self, context: dict[str, Any]) -> LambdaRuntimeResult:
        """Check if a runtime or network is ready."""
        from mcard.ptr.core.runtime import RuntimeFactory
        runtime_name = context.get('runtime_name', 'lambda')

        # Get status for all runtimes
        status_map = RuntimeFactory.get_detailed_status()

        if runtime_name == 'all':
            available = all(s['available'] for s in status_map.values())
            return LambdaRuntimeResult(
                success=True,
                pretty_print=f"All Runtimes Ready: {available}",
                is_closed=available
            )

        status = status_map.get(runtime_name.lower())
        if not status:
            return LambdaRuntimeResult(success=False, error=f"Unknown runtime: {runtime_name}")

        return LambdaRuntimeResult(
            success=True,
            pretty_print=f"Runtime {runtime_name} status: {status['available']}",
            is_closed=status['available']
        )

    def _numeric_op(self, operation: str, context: dict[str, Any]) -> LambdaRuntimeResult:
        """Perform a built-in numeric operation."""
        a = context.get('a', 0)
        b = context.get('b', 0)

        try:
            val_a = float(a)
            val_b = float(b)

            if operation == 'num-add':
                result = val_a + val_b
            elif operation == 'num-sub':
                result = val_a - val_b
            elif operation == 'num-mul':
                result = val_a * val_b
            elif operation == 'num-div':
                if val_b == 0:
                    return LambdaRuntimeResult(success=False, error="Division by zero")
                result = val_a / val_b
            else:
                return LambdaRuntimeResult(success=False, error=f"Unknown numeric op: {operation}")

            # Convert result back to string for pretty print
            res_str = str(int(result) if result.is_integer() else result)
            return LambdaRuntimeResult(
                success=True,
                pretty_print=res_str
            )
        except (ValueError, TypeError):
            return LambdaRuntimeResult(success=False, error="Invalid numeric inputs")

    def _http_request(self, context: dict[str, Any]) -> LambdaRuntimeResult:
        """Perform a built-in network request."""
        from mcard.ptr.core.runtime import RuntimeFactory
        net_executor = RuntimeFactory.get_executor('network')
        if not net_executor:
            return LambdaRuntimeResult(success=False, error="Network runtime not available")

        # Forward request to NetworkRuntime
        # We need a dummy target as execute expects it
        from mcard import MCard
        dummy_target = MCard("dummy")

        # Build config from context
        config = {
            'method': context.get('method', 'GET'),
            'url': context.get('url'),
            'headers': context.get('headers', {}),
            'body': context.get('body')
        }

        if not config['url']:
            return LambdaRuntimeResult(success=False, error="No URL provided for http-request")

        try:
            res = net_executor.execute({}, dummy_target, config)
            return LambdaRuntimeResult(
                success=True,
                pretty_print=str(res)
            )
        except Exception as e:
            return LambdaRuntimeResult(success=False, error=f"Network error: {str(e)}")

    def _church_to_int(self, term_hash: str) -> LambdaRuntimeResult:
        """
        Decode a Church numeral to a regular integer.

        Church numeral n = λf.λx.f^n(x) where f is applied n times.

        Algorithm:
        1. Normalize the term first
        2. Expect form: Abs(f, Abs(x, body))
        3. Count how many times 'f' appears in application position in body
        """
        try:
            # First normalize the term
            result = normalize(self.collection, term_hash, 'normal', 1000)

            if result is None:
                return LambdaRuntimeResult(success=False, error="Failed to normalize term")

            pretty = pretty_print_deep(self.collection, result.normal_form)

            # Decode Church numeral structure: λf.λx.body
            count = self._count_church_applications(result.normal_form)

            return LambdaRuntimeResult(
                success=True,
                term_hash=result.normal_form,
                pretty_print=f"{count} (Church: {pretty})"
            )
        except Exception as e:
            return LambdaRuntimeResult(success=False, error=f"Church decode error: {str(e)}")

    def _count_church_applications(self, term_hash: str) -> int:
        """
        Count applications in a Church numeral body.
        Church numeral n has the form: λf.λx.f(f(f(...f(x)...)))
        where f appears n times.
        """
        term = load_term(self.collection, term_hash)
        if term is None:
            return -1

        # Expect: Abs(f, Abs(x, body))
        if not isinstance(term, AbsTerm):
            return -1

        f_var = term.param
        inner_term = load_term(self.collection, term.body)

        if inner_term is None or not isinstance(inner_term, AbsTerm):
            return -1

        x_var = inner_term.param

        # Count how many times we see App(f, ...) wrapping
        count = 0
        current_hash = inner_term.body

        while True:
            body = load_term(self.collection, current_hash)
            if body is None:
                break

            if isinstance(body, AppTerm):
                func = load_term(self.collection, body.func)

                # Check if function is the 'f' variable
                if func and isinstance(func, VarTerm) and func.name == f_var:
                    count += 1
                    current_hash = body.arg
                else:
                    # Not a simple Church numeral structure
                    break
            elif isinstance(body, VarTerm) and body.name == x_var:
                # Reached the base case 'x'
                return count
            else:
                break

        return count
