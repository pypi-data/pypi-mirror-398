"""
CLM Monadic Template - The Genesis Protocol
===========================================

This template operationalizes the "Prologue of Spacetime" by defining the 
Cubical Logic Model (CLM) and Narrative Structure as a Monadic Computation.

It integrates:
1.  **CLM Dimensions**: Abstract (VCard), Concrete (PCard), Balanced (MCard).
2.  **Monadic Thread**: Reader (Context), State (World), Writer (Log), IO (Effects).
3.  **Narrative Execution**: Composing chapters as functional transformations.

Usage:
    Use this template to define the logic for each Chapter of the Prologue.
    Each Chapter is a function: Context -> State -> (Result, NewState, Log).
"""

from typing import Generic, TypeVar, Callable, Tuple, Any, List, Dict, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import datetime

# Type Variables
T = TypeVar('T')  # Result Type
U = TypeVar('U')  # Transformed Result Type
R = TypeVar('R')  # Reader Context Type
S = TypeVar('S')  # State Type
W = TypeVar('W')  # Writer Log Type

# =============================================================================
# 1. The Monad Archetype
# =============================================================================

class Monad(Generic[T], ABC):
    """
    The Archetype of the Function.
    Encapsulates Purity, Manages Impurity, Enables Composition.
    """
    @abstractmethod
    def bind(self, func: Callable[[T], 'Monad[U]']) -> 'Monad[U]':
        pass

    @classmethod
    @abstractmethod
    def unit(cls, value: T) -> 'Monad[T]':
        pass

# =============================================================================
# 2. The Narrative Threads (Specific Monads)
# =============================================================================

@dataclass
class Reader(Monad[T], Generic[R, T]):
    """
    The Reader Monad: Carries the Cultural Context and Configuration.
    Immutable and accessible everywhere.
    """
    run: Callable[[R], T]

    def bind(self, func: Callable[[T], 'Reader[R, U]']) -> 'Reader[R, U]':
        return Reader(lambda r: func(self.run(r)).run(r))

    @classmethod
    def unit(cls, value: T) -> 'Reader[R, T]':
        return Reader(lambda _: value)

@dataclass
class State(Monad[T], Generic[S, T]):
    """
    The State Monad: Carries the evolving World State.
    (Village Prosperity, Network Topology, User Progress).
    """
    run: Callable[[S], Tuple[T, S]]

    def bind(self, func: Callable[[T], 'State[S, U]']) -> 'State[S, U]':
        def new_run(s: S) -> Tuple[U, S]:
            val, new_s = self.run(s)
            return func(val).run(new_s)
        return State(new_run)

    @classmethod
    def unit(cls, value: T) -> 'State[S, T]':
        return State(lambda s: (value, s))

@dataclass
class Writer(Monad[T], Generic[W, T]):
    """
    The Writer Monad: Accumulates the Log of the journey.
    (The Story Text, The Audit Trail).
    """
    run: Tuple[T, List[W]]

    def bind(self, func: Callable[[T], 'Writer[W, U]']) -> 'Writer[W, U]':
        val, log = self.run
        new_writer = func(val)
        new_val, new_log = new_writer.run
        return Writer((new_val, log + new_log))

    @classmethod
    def unit(cls, value: T) -> 'Writer[W, T]':
        return Writer((value, []))

@dataclass
class IO(Monad[T]):
    """
    The IO Monad: Handles Effects at the boundaries.
    (User Interaction, System Deployment).
    """
    effect: Callable[[], T]

    def bind(self, func: Callable[[T], 'IO[U]']) -> 'IO[U]':
        return IO(lambda: func(self.effect()).effect())

    @classmethod
    def unit(cls, value: T) -> 'IO[T]':
        return IO(lambda: value)

@dataclass
class Either(Monad[T], Generic[T]):
    """
    The Either Monad: Represents a value that can be one of two types.
    Used for Error Handling (Left=Error, Right=Success) or Branching Logic.
    """
    value: Any
    is_left: bool

    @property
    def is_right(self) -> bool:
        return not self.is_left

    def bind(self, func: Callable[[T], 'Either[U]']) -> 'Either[U]':
        if self.is_left:
            return self  # Propagate failure/left value
        return func(self.value)

    @classmethod
    def unit(cls, value: T) -> 'Either[T]':
        return Either(value, is_left=False)

    @classmethod
    def left(cls, value: Any) -> 'Either[Any]':
        return Either(value, is_left=True)

    @classmethod
    def right(cls, value: T) -> 'Either[T]':
        return Either(value, is_left=False)

@dataclass
class Maybe(Monad[T], Generic[T]):
    """
    The Maybe Monad: Represents an optional value (Just val or Nothing).
    Used for handling absence of value without null checks.
    """
    value: Optional[T]
    is_nothing: bool

    @property
    def is_just(self) -> bool:
        return not self.is_nothing

    def bind(self, func: Callable[[T], 'Maybe[U]']) -> 'Maybe[U]':
        if self.is_nothing:
            return self  # Propagate Nothing
        return func(self.value)

    @classmethod
    def unit(cls, value: T) -> 'Maybe[T]':
        return Maybe(value, is_nothing=False)

    @classmethod
    def nothing(cls) -> 'Maybe[Any]':
        return Maybe(None, is_nothing=True)

    @classmethod
    def just(cls, value: T) -> 'Maybe[T]':
        return Maybe(value, is_nothing=False)

# =============================================================================
# 3. The Cubical Logic Model (CLM)
# =============================================================================

@dataclass
class CLMConfiguration:
    """
    Defines the three orthogonal dimensions of any well-formed concept.
    """
    abstract: str   # VCard (Value/Type): The Principle ("Why")
    concrete: str   # PCard (Process/Instance): The Character ("How")
    balanced: str   # MCard (Memory/Property): The Evidence ("What")

    def __repr__(self):
        return (f"🧊 CLM Cube:\n"
                f"  - Abstract (Why): {self.abstract}\n"
                f"  - Concrete (How): {self.concrete}\n"
                f"  - Balanced (What): {self.balanced}")

# =============================================================================
# 4. The Narrative Monad (Composition)
# =============================================================================

class NarrativeMonad(Generic[R, S, W, T]):
    """
    The 'Spacetime' Monad.
    A composition of Reader, State, Writer, and IO.
    
    Signature: Context -> State -> IO(Result, NewState, Log)
    """
    def __init__(self, run: Callable[[R, S], IO[Tuple[T, S, List[W]]]]):
        self.run = run

    def bind(self, func: Callable[[T], 'NarrativeMonad[R, S, W, U]']) -> 'NarrativeMonad[R, S, W, U]':
        def new_run(r: R, s: S) -> IO[Tuple[U, S, List[W]]]:
            # Execute first step
            io_result = self.run(r, s)
            
            # Define continuation inside IO to handle effects sequentially
            def continuation() -> Tuple[U, S, List[W]]:
                val, s_prime, log1 = io_result.effect()
                
                # Execute second step
                next_monad = func(val)
                io_result2 = next_monad.run(r, s_prime)
                val2, s_double_prime, log2 = io_result2.effect()
                
                return (val2, s_double_prime, log1 + log2)
            
            return IO(continuation)
        
        return NarrativeMonad(new_run)

    @classmethod
    def unit(cls, value: T) -> 'NarrativeMonad[R, S, W, T]':
        return NarrativeMonad(lambda r, s: IO.unit((value, s, [])))
    
    @classmethod
    def lift_io(cls, io_action: IO[T]) -> 'NarrativeMonad[R, S, W, T]':
        """Lift a pure IO action into the Narrative Monad"""
        return NarrativeMonad(lambda r, s: IO(lambda: (io_action.effect(), s, [])))

    @classmethod
    def log(cls, message: W) -> 'NarrativeMonad[R, S, W, None]':
        """Log a message (Writer effect)"""
        return NarrativeMonad(lambda r, s: IO.unit((None, s, [message])))

    @classmethod
    def get_context(cls) -> 'NarrativeMonad[R, S, W, R]':
        """Read the context (Reader effect)"""
        return NarrativeMonad(lambda r, s: IO.unit((r, s, [])))

    @classmethod
    def get_state(cls) -> 'NarrativeMonad[R, S, W, S]':
        """Read the state (State effect)"""
        return NarrativeMonad(lambda r, s: IO.unit((s, s, [])))

    @classmethod
    def put_state(cls, new_state: S) -> 'NarrativeMonad[R, S, W, None]':
        """Update the state (State effect)"""
        return NarrativeMonad(lambda r, s: IO.unit((None, new_state, [])))

    def execute(self, context: R, initial_state: S) -> Tuple[T, S, List[W]]:
        """Run the monadic chain"""
        return self.run(context, initial_state).effect()

# =============================================================================
# 5. Chapter Template
# =============================================================================

@dataclass
class Chapter:
    """
    A Chapter in the Prologue of Spacetime.
    """
    id: int
    title: str
    clm: CLMConfiguration
    mvp_card: str  # The Archetype Name
    pkc_task: str  # The Container Task
    action: NarrativeMonad[Dict, Dict, str, Any]

    def run(self, context: Dict, state: Dict) -> Tuple[Any, Dict, List[str]]:
        print(f"\n--- Executing {self.title} ---")
        print(self.clm)
        result, new_state, log = self.action.execute(context, state)
        print(f"Result: {result}")
        print(f"Log: {log}")
        return result, new_state, log

# =============================================================================
# End of Monadic Template
# =============================================================================

