"""
CLM Action Monad - Composable Actions following Monad Laws.

This module implements the Action monad for CLM, enabling composable
agent actions that follow the three Monad Laws:

1. Left Identity:   return a >>= f  ≡  f a
2. Right Identity:  m >>= return    ≡  m  
3. Associativity:   (m >>= f) >>= g ≡  m >>= (λx. f x >>= g)

Actions are the atomic units of computation in CLM workflows.
Each action transforms context and produces a result while
accumulating effects (memory updates, tool calls, logs).

Aligned with the Lambda Calculus interpretation:
- α-conversion: Action renaming (identity preservation)
- β-reduction: Action execution (input substitution)
- η-conversion: Behavioral equivalence (same I/O behavior)
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any, Awaitable, Callable, Dict, Generic, List, Optional, 
    Tuple, TypeVar, Union
)

from mcard import MCard


logger = logging.getLogger(__name__)


# Type variables for generic Action monad
A = TypeVar('A')  # Input type
B = TypeVar('B')  # Output type
C = TypeVar('C')  # Third type for composition


class ActionStatus(Enum):
    """Status of an action execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"


@dataclass
class ActionContext:
    """Context passed to actions during execution.
    
    This is the Reader monad component - read-only configuration
    and environment that flows through the action pipeline.
    """
    # Session information
    session_id: str = ""
    agent_id: str = ""
    
    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)
    secrets: Dict[str, str] = field(default_factory=dict)
    
    # Input parameters (from CLM params interpolation)
    params: Dict[str, Any] = field(default_factory=dict)
    
    # Execution metadata
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))
    trace_id: str = ""
    
    def with_params(self, params: Dict[str, Any]) -> "ActionContext":
        """Create a new context with updated params."""
        return ActionContext(
            session_id=self.session_id,
            agent_id=self.agent_id,
            config={**self.config},
            secrets={**self.secrets},
            params={**self.params, **params},
            timestamp=self.timestamp,
            trace_id=self.trace_id
        )


@dataclass
class ActionEffect:
    """Side effects produced by an action.
    
    This is the Writer monad component - accumulated effects
    that flow through the action pipeline.
    """
    # Memory updates (MCards to store)
    memory_updates: List[MCard] = field(default_factory=list)
    
    # Tool calls made
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    
    # Audit log entries
    logs: List[str] = field(default_factory=list)
    
    # Token usage (for LLM actions)
    tokens: Dict[str, int] = field(default_factory=lambda: {"prompt": 0, "completion": 0})
    
    # Execution time (ms)
    execution_time: int = 0
    
    def __add__(self, other: "ActionEffect") -> "ActionEffect":
        """Combine two effects (monoid append)."""
        return ActionEffect(
            memory_updates=self.memory_updates + other.memory_updates,
            tool_calls=self.tool_calls + other.tool_calls,
            logs=self.logs + other.logs,
            tokens={
                "prompt": self.tokens["prompt"] + other.tokens["prompt"],
                "completion": self.tokens["completion"] + other.tokens["completion"]
            },
            execution_time=self.execution_time + other.execution_time
        )
    
    @staticmethod
    def empty() -> "ActionEffect":
        """Create an empty effect (monoid identity)."""
        return ActionEffect()


@dataclass
class ActionResult(Generic[A]):
    """Result of an action execution.
    
    Combines the computed value with accumulated effects.
    This is the full monad: Reader + Writer + Either.
    """
    success: bool
    value: Optional[A] = None
    error: Optional[str] = None
    effects: ActionEffect = field(default_factory=ActionEffect)
    
    def map(self, f: Callable[[A], B]) -> "ActionResult[B]":
        """Functor map: Apply function to value if successful."""
        if self.success and self.value is not None:
            try:
                return ActionResult(
                    success=True,
                    value=f(self.value),
                    effects=self.effects
                )
            except Exception as e:
                return ActionResult(
                    success=False,
                    error=str(e),
                    effects=self.effects
                )
        return ActionResult(
            success=False,
            error=self.error,
            effects=self.effects
        )
    
    @staticmethod
    def pure(value: A) -> "ActionResult[A]":
        """Lift a pure value into ActionResult (return/unit)."""
        return ActionResult(success=True, value=value)
    
    @staticmethod
    def fail(error: str) -> "ActionResult[A]":
        """Create a failed result."""
        return ActionResult(success=False, error=error)


# Action type: A function from context to async result
ActionFn = Callable[[ActionContext], Awaitable[ActionResult[A]]]


class Action(Generic[A]):
    """
    The Action Monad - A composable unit of computation.
    
    An Action encapsulates:
    - An async function from context to result
    - The ability to compose with other actions (bind/flatMap)
    - Effects accumulated during execution (Writer)
    - Context propagation (Reader)
    - Error handling (Either)
    
    Satisfies the Monad Laws:
    
    1. Left Identity:  Action.pure(a).bind(f) == f(a)
    2. Right Identity: m.bind(Action.pure) == m
    3. Associativity:  m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))
    """
    
    def __init__(self, run: ActionFn[A]):
        """
        Create an action from a function.
        
        Args:
            run: Async function (ActionContext -> ActionResult[A])
        """
        self._run = run
    
    async def execute(self, ctx: ActionContext) -> ActionResult[A]:
        """
        Execute this action with the given context.
        
        Args:
            ctx: The execution context
            
        Returns:
            The result of the action
        """
        start_time = time.time()
        try:
            result = await self._run(ctx)
            # Add execution time to effects
            elapsed = int((time.time() - start_time) * 1000)
            result.effects.execution_time += elapsed
            return result
        except Exception as e:
            elapsed = int((time.time() - start_time) * 1000)
            return ActionResult(
                success=False,
                error=str(e),
                effects=ActionEffect(execution_time=elapsed, logs=[f"Exception: {e}"])
            )
    
    def bind(self, f: Callable[[A], "Action[B]"]) -> "Action[B]":
        """
        Monadic bind (>>=, flatMap).
        
        Sequences this action with a function that produces
        another action based on this action's result.
        
        This is the KEY operation that makes Action a monad.
        
        Args:
            f: Function from A to Action[B]
            
        Returns:
            A new action that chains the computations
        """
        async def bound_run(ctx: ActionContext) -> ActionResult[B]:
            # Execute this action
            result_a = await self.execute(ctx)
            
            if not result_a.success:
                # Propagate failure with accumulated effects
                return ActionResult(
                    success=False,
                    error=result_a.error,
                    effects=result_a.effects
                )
            
            # Apply f to get the next action
            action_b = f(result_a.value)
            
            # Execute the next action
            result_b = await action_b.execute(ctx)
            
            # Combine effects from both actions
            combined_effects = result_a.effects + result_b.effects
            
            return ActionResult(
                success=result_b.success,
                value=result_b.value,
                error=result_b.error,
                effects=combined_effects
            )
        
        return Action(bound_run)
    
    def map(self, f: Callable[[A], B]) -> "Action[B]":
        """
        Functor map.
        
        Apply a pure function to the action's result.
        
        Args:
            f: Pure function from A to B
            
        Returns:
            A new action with the transformed result
        """
        return self.bind(lambda a: Action.pure(f(a)))
    
    def then(self, next_action: "Action[B]") -> "Action[B]":
        """
        Sequence with another action, ignoring this result.
        
        Useful for side-effect-only actions.
        
        Args:
            next_action: The action to execute after this one
            
        Returns:
            The result of next_action
        """
        return self.bind(lambda _: next_action)
    
    @staticmethod
    def pure(value: A) -> "Action[A]":
        """
        Lift a pure value into Action (return/unit).
        
        This is the 'return' operation of the monad.
        
        Satisfies Left Identity: pure(a).bind(f) == f(a)
        Satisfies Right Identity: m.bind(pure) == m
        
        Args:
            value: The value to lift
            
        Returns:
            An action that immediately succeeds with the value
        """
        async def pure_run(ctx: ActionContext) -> ActionResult[A]:
            return ActionResult.pure(value)
        
        return Action(pure_run)
    
    @staticmethod
    def fail(error: str) -> "Action[A]":
        """
        Create a failing action.
        
        Args:
            error: The error message
            
        Returns:
            An action that immediately fails
        """
        async def fail_run(ctx: ActionContext) -> ActionResult[A]:
            return ActionResult.fail(error)
        
        return Action(fail_run)
    
    @staticmethod
    def ask() -> "Action[ActionContext]":
        """
        Reader monad operation: Get the current context.
        
        Returns:
            An action that returns the context
        """
        async def ask_run(ctx: ActionContext) -> ActionResult[ActionContext]:
            return ActionResult.pure(ctx)
        
        return Action(ask_run)
    
    @staticmethod
    def asks(f: Callable[[ActionContext], A]) -> "Action[A]":
        """
        Reader monad operation: Apply function to context.
        
        Args:
            f: Function to apply to context
            
        Returns:
            An action that returns f(context)
        """
        return Action.ask().map(f)
    
    @staticmethod
    def tell(effect: ActionEffect) -> "Action[None]":
        """
        Writer monad operation: Emit an effect.
        
        Args:
            effect: The effect to emit
            
        Returns:
            An action that emits the effect
        """
        async def tell_run(ctx: ActionContext) -> ActionResult[None]:
            return ActionResult(success=True, value=None, effects=effect)
        
        return Action(tell_run)
    
    @staticmethod
    def log(message: str) -> "Action[None]":
        """
        Convenience: Log a message.
        
        Args:
            message: The log message
            
        Returns:
            An action that logs the message
        """
        return Action.tell(ActionEffect(logs=[message]))
    
    @staticmethod
    def from_async(f: Callable[[ActionContext], Awaitable[A]]) -> "Action[A]":
        """
        Create an action from an async function.
        
        Args:
            f: Async function (ctx -> A)
            
        Returns:
            An action wrapping the function
        """
        async def wrapped(ctx: ActionContext) -> ActionResult[A]:
            try:
                result = await f(ctx)
                return ActionResult.pure(result)
            except Exception as e:
                return ActionResult.fail(str(e))
        
        return Action(wrapped)
    
    @staticmethod
    def from_sync(f: Callable[[ActionContext], A]) -> "Action[A]":
        """
        Create an action from a synchronous function.
        
        Args:
            f: Sync function (ctx -> A)
            
        Returns:
            An action wrapping the function
        """
        async def wrapped(ctx: ActionContext) -> ActionResult[A]:
            try:
                result = f(ctx)
                return ActionResult.pure(result)
            except Exception as e:
                return ActionResult.fail(str(e))
        
        return Action(wrapped)


# ============ Action Composition Utilities ============

def sequence(actions: List[Action[A]]) -> Action[List[A]]:
    """
    Sequence a list of actions, collecting results.
    
    Args:
        actions: List of actions to sequence
        
    Returns:
        An action that produces a list of results
    """
    if not actions:
        return Action.pure([])
    
    async def seq_run(ctx: ActionContext) -> ActionResult[List[A]]:
        results: List[A] = []
        combined_effects = ActionEffect.empty()
        
        for action in actions:
            result = await action.execute(ctx)
            combined_effects = combined_effects + result.effects
            
            if not result.success:
                return ActionResult(
                    success=False,
                    error=result.error,
                    effects=combined_effects
                )
            
            results.append(result.value)
        
        return ActionResult(
            success=True,
            value=results,
            effects=combined_effects
        )
    
    return Action(seq_run)


def parallel(actions: List[Action[A]]) -> Action[List[A]]:
    """
    Execute actions in parallel, collecting results.
    
    Args:
        actions: List of actions to execute in parallel
        
    Returns:
        An action that produces a list of results
    """
    if not actions:
        return Action.pure([])
    
    async def par_run(ctx: ActionContext) -> ActionResult[List[A]]:
        # Execute all actions concurrently
        tasks = [action.execute(ctx) for action in actions]
        results = await asyncio.gather(*tasks)
        
        # Combine effects and check for failures
        combined_effects = ActionEffect.empty()
        values: List[A] = []
        
        for result in results:
            combined_effects = combined_effects + result.effects
            if not result.success:
                return ActionResult(
                    success=False,
                    error=result.error,
                    effects=combined_effects
                )
            values.append(result.value)
        
        return ActionResult(
            success=True,
            value=values,
            effects=combined_effects
        )
    
    return Action(par_run)


def kleisli_compose(
    f: Callable[[A], Action[B]],
    g: Callable[[B], Action[C]]
) -> Callable[[A], Action[C]]:
    """
    Kleisli composition: Compose two monadic functions.
    
    (g <=< f)(a) = f(a).bind(g)
    
    This is the categorical composition in the Kleisli category.
    
    Args:
        f: First Kleisli arrow (A -> Action[B])
        g: Second Kleisli arrow (B -> Action[C])
        
    Returns:
        Composed Kleisli arrow (A -> Action[C])
    """
    def composed(a: A) -> Action[C]:
        return f(a).bind(g)
    
    return composed


def identity_action() -> Callable[[A], Action[A]]:
    """
    The identity Kleisli arrow.
    
    This is Action.pure, serving as the identity for Kleisli composition.
    
    Returns:
        The identity function in the Kleisli category
    """
    return Action.pure


# ============ Monad Law Verification ============

async def verify_left_identity(a: A, f: Callable[[A], Action[B]], ctx: ActionContext) -> bool:
    """
    Verify Left Identity law: pure(a).bind(f) == f(a)
    
    Args:
        a: A value
        f: A Kleisli arrow
        ctx: Execution context
        
    Returns:
        True if the law holds
    """
    left = await Action.pure(a).bind(f).execute(ctx)
    right = await f(a).execute(ctx)
    
    return (left.success == right.success and 
            left.value == right.value and
            left.error == right.error)


async def verify_right_identity(m: Action[A], ctx: ActionContext) -> bool:
    """
    Verify Right Identity law: m.bind(pure) == m
    
    Args:
        m: An action
        ctx: Execution context
        
    Returns:
        True if the law holds
    """
    left = await m.bind(Action.pure).execute(ctx)
    right = await m.execute(ctx)
    
    return (left.success == right.success and
            left.value == right.value and
            left.error == right.error)


async def verify_associativity(
    m: Action[A],
    f: Callable[[A], Action[B]],
    g: Callable[[B], Action[C]],
    ctx: ActionContext
) -> bool:
    """
    Verify Associativity law: (m.bind(f)).bind(g) == m.bind(lambda x: f(x).bind(g))
    
    Args:
        m: An action
        f: First Kleisli arrow
        g: Second Kleisli arrow
        ctx: Execution context
        
    Returns:
        True if the law holds
    """
    left = await m.bind(f).bind(g).execute(ctx)
    right = await m.bind(lambda x: f(x).bind(g)).execute(ctx)
    
    return (left.success == right.success and
            left.value == right.value and
            left.error == right.error)


# ============ Pre/Post Condition Contract System ============

@dataclass
class Condition(Generic[A]):
    """
    A condition that can be evaluated against context or result.
    
    Conditions form the basis of Hoare Logic contracts:
    {P} Action {Q} where P = preconditions, Q = postconditions
    """
    name: str
    expression: str  # Human-readable description
    check: Callable[[A], bool]  # Executable predicate


@dataclass
class ActionContract(Generic[A]):
    """
    Contract defining pre/post conditions for an Action.
    
    Implements Hoare triple: {Preconditions} Action {Postconditions}
    """
    preconditions: List[Condition[ActionContext]]
    postconditions: List[Condition["ActionResult[A]"]]
    invariants: List[Condition[Any]] = field(default_factory=list)


@dataclass
class ConditionResult:
    """Result of verifying a single condition."""
    name: str
    expression: str
    satisfied: bool
    error: Optional[str] = None


@dataclass
class ContractVerification:
    """Result of contract verification for a phase."""
    phase: str  # 'pre' or 'post'
    conditions: List[ConditionResult]
    all_satisfied: bool
    timestamp: int


@dataclass
class VCardPair:
    """
    VCard pair produced by contract verification.
    
    This represents the verification evidence for an Action execution:
    - PreCondition VCard: Certifies input requirements were met
    - PostCondition VCard: Certifies output guarantees were met
    """
    pre_condition_vcard: str   # MCard hash
    post_condition_vcard: str  # MCard hash
    action_hash: str           # Hash of action definition
    linked_at: int             # Timestamp of linking


@dataclass
class ContractExecutionResult(Generic[A]):
    """Result of contract-aware execution."""
    result: ActionResult[A]
    vcard_pair: VCardPair
    pre_verification: ContractVerification
    post_verification: ContractVerification


class ContractAction(Action[A]):
    """
    Contract-aware Action that produces VCard pairs.
    
    Extends the base Action monad with Hoare Logic contracts:
    - Verifies preconditions before execution
    - Verifies postconditions after execution
    - Produces VCard pair as verification evidence
    """
    
    def __init__(self, run: Callable[[ActionContext], Awaitable[ActionResult[A]]], 
                 contract: ActionContract[A]):
        super().__init__(run)
        self._contract = contract
    
    @property
    def contract(self) -> ActionContract[A]:
        """Get the contract for this action."""
        return self._contract
    
    def verify_preconditions(self, ctx: ActionContext) -> ContractVerification:
        """Verify preconditions against the context."""
        conditions: List[ConditionResult] = []
        
        for cond in self._contract.preconditions:
            try:
                satisfied = cond.check(ctx)
                conditions.append(ConditionResult(
                    name=cond.name,
                    expression=cond.expression,
                    satisfied=satisfied
                ))
            except Exception as e:
                conditions.append(ConditionResult(
                    name=cond.name,
                    expression=cond.expression,
                    satisfied=False,
                    error=str(e)
                ))
        
        return ContractVerification(
            phase='pre',
            conditions=conditions,
            all_satisfied=all(c.satisfied for c in conditions),
            timestamp=int(time.time() * 1000)
        )
    
    def verify_postconditions(self, result: ActionResult[A]) -> ContractVerification:
        """Verify postconditions against the result."""
        conditions: List[ConditionResult] = []
        
        for cond in self._contract.postconditions:
            try:
                satisfied = cond.check(result)
                conditions.append(ConditionResult(
                    name=cond.name,
                    expression=cond.expression,
                    satisfied=satisfied
                ))
            except Exception as e:
                conditions.append(ConditionResult(
                    name=cond.name,
                    expression=cond.expression,
                    satisfied=False,
                    error=str(e)
                ))
        
        return ContractVerification(
            phase='post',
            conditions=conditions,
            all_satisfied=all(c.satisfied for c in conditions),
            timestamp=int(time.time() * 1000)
        )
    
    def create_pre_condition_vcard(self, verification: ContractVerification, 
                                   action_hash: str) -> str:
        """
        Create a PreCondition VCard from verification result.
        Returns a hash representing the VCard.
        """
        # In production: store as MCard and return hash
        return f"vcard:pre:{action_hash}:{verification.timestamp}"
    
    def create_post_condition_vcard(self, verification: ContractVerification,
                                    action_hash: str, pre_vcard_hash: str,
                                    result: ActionResult[A]) -> str:
        """
        Create a PostCondition VCard from verification result.
        Links back to the PreCondition VCard.
        """
        # In production: store as MCard and return hash
        return f"vcard:post:{action_hash}:{verification.timestamp}"
    
    def get_action_hash(self) -> str:
        """Generate a hash for this action (based on contract)."""
        contract_summary = {
            'pre_conditions': [c.name for c in self._contract.preconditions],
            'post_conditions': [c.name for c in self._contract.postconditions]
        }
        return f"action:{json.dumps(contract_summary)}"[:64]
    
    async def execute_with_contract(self, ctx: ActionContext) -> ContractExecutionResult[A]:
        """
        Execute with full contract verification, producing VCard pair.
        
        This is the primary method for contract-aware execution:
        1. Verify preconditions → create PreCondition VCard
        2. Execute action (only if preconditions pass)
        3. Verify postconditions → create PostCondition VCard
        4. Return result with VCard pair
        """
        action_hash = self.get_action_hash()
        
        # Phase 1: Verify preconditions
        pre_verification = self.verify_preconditions(ctx)
        pre_vcard = self.create_pre_condition_vcard(pre_verification, action_hash)
        
        # If preconditions fail, return early with failure
        if not pre_verification.all_satisfied:
            failed_conditions = ', '.join(
                c.name for c in pre_verification.conditions if not c.satisfied
            )
            
            failed_result = ActionResult.fail(f"Precondition failed: {failed_conditions}")
            post_verification = ContractVerification(
                phase='post',
                conditions=[],
                all_satisfied=False,
                timestamp=int(time.time() * 1000)
            )
            
            return ContractExecutionResult(
                result=failed_result,
                vcard_pair=VCardPair(
                    pre_condition_vcard=pre_vcard,
                    post_condition_vcard='',
                    action_hash=action_hash,
                    linked_at=int(time.time() * 1000)
                ),
                pre_verification=pre_verification,
                post_verification=post_verification
            )
        
        # Phase 2: Execute action
        result = await self.execute(ctx)
        
        # Phase 3: Verify postconditions
        if result.success:
            post_verification = self.verify_postconditions(result)
        else:
            post_verification = ContractVerification(
                phase='post',
                conditions=[],
                all_satisfied=False,
                timestamp=int(time.time() * 1000)
            )
        
        post_vcard = self.create_post_condition_vcard(
            post_verification, action_hash, pre_vcard, result
        )
        
        return ContractExecutionResult(
            result=result,
            vcard_pair=VCardPair(
                pre_condition_vcard=pre_vcard,
                post_condition_vcard=post_vcard,
                action_hash=action_hash,
                linked_at=int(time.time() * 1000)
            ),
            pre_verification=pre_verification,
            post_verification=post_verification
        )
    
    def bind_with_contract(self, f: Callable[[A], "ContractAction[B]"]) -> "ContractAction[B]":
        """Compose contract-aware actions, chaining VCard pairs."""
        # Merged contract: preconditions from self, postconditions from f's result
        merged_contract: ActionContract[B] = ActionContract(
            preconditions=self._contract.preconditions,
            postconditions=[]  # Will be filled by the bound action
        )
        
        async def bound_run(ctx: ActionContext) -> ActionResult[B]:
            result_a = await self.execute(ctx)
            
            if not result_a.success:
                return ActionResult(
                    success=False,
                    error=result_a.error,
                    effects=result_a.effects
                )
            
            action_b = f(result_a.value)
            result_b = await action_b.execute(ctx)
            
            return ActionResult(
                success=result_b.success,
                value=result_b.value,
                error=result_b.error,
                effects=result_a.effects + result_b.effects
            )
        
        return ContractAction(bound_run, merged_contract)
    
    @staticmethod
    def pure_with_contract(value: A, contract: Optional[ActionContract[A]] = None) -> "ContractAction[A]":
        """Create a contract-aware action from a pure value."""
        default_contract: ActionContract[A] = contract or ActionContract(
            preconditions=[],
            postconditions=[Condition(
                name='has_value',
                expression='result.value is not None',
                check=lambda r: r.value is not None
            )]
        )
        
        async def pure_run(ctx: ActionContext) -> ActionResult[A]:
            return ActionResult.pure(value)
        
        return ContractAction(pure_run, default_contract)
    
    @staticmethod
    def from_async_with_contract(
        f: Callable[[ActionContext], Awaitable[A]],
        contract: ActionContract[A]
    ) -> "ContractAction[A]":
        """Create a contract-aware action from an async function."""
        async def wrapped(ctx: ActionContext) -> ActionResult[A]:
            try:
                result = await f(ctx)
                return ActionResult.pure(result)
            except Exception as e:
                return ActionResult.fail(str(e))
        
        return ContractAction(wrapped, contract)
