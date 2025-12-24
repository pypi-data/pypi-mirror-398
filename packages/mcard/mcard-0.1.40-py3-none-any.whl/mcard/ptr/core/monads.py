"""
Monadic definitions for the PTR Core system.
Aligns with the Monad design pattern: IO, State, Reader, Writer, Maybe, Either.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Callable, Any, List, Union, Tuple, Optional
from dataclasses import dataclass

T = TypeVar('T')
U = TypeVar('U')
E = TypeVar('E')  # Error or Environment or State type
L = TypeVar('L')  # Log type

class Monad(Generic[T], ABC):
    """Abstract Base Class for Monads"""
    
    @abstractmethod
    def bind(self, func: Callable[[T], 'Monad[U]']) -> 'Monad[U]':
        """Also known as flatMap or >>=."""
        pass

    def map(self, func: Callable[[T], U]) -> 'Monad[U]':
        """Standard map operation."""
        return self.bind(lambda x: self.pure(func(x)))

    @classmethod
    @abstractmethod
    def pure(cls, value: T) -> 'Monad[T]':
        """Wraps a value in the Monad context."""
        pass

# --- Either Monad (Error Handling) ---

class Either(Monad[T], Generic[E, T]):
    """Represents a value of one of two possible types (a disjoint union)."""
    
    def is_left(self) -> bool:
        raise NotImplementedError
        
    def is_right(self) -> bool:
        raise NotImplementedError

    @classmethod
    def pure(cls, value: T) -> 'Either[E, T]':
        return Right(value)

@dataclass
class Left(Either[E, T]):
    value: E
    
    def is_left(self) -> bool: return True
    def is_right(self) -> bool: return False
    
    def bind(self, func: Callable[[T], 'Monad[U]']) -> 'Monad[U]':
        return self  # Propagate error
        
    def map(self, func: Callable[[T], U]) -> 'Monad[U]':
        return self

@dataclass
class Right(Either[E, T]):
    value: T
    
    def is_left(self) -> bool: return False
    def is_right(self) -> bool: return True
    
    def bind(self, func: Callable[[T], 'Monad[U]']) -> 'Monad[U]':
        return func(self.value)

# --- Maybe Monad (Optional Values) ---

class Maybe(Monad[T]):
    """Represents an optional value."""
    
    @classmethod
    def pure(cls, value: T) -> 'Maybe[T]':
        return Just(value)

@dataclass
class Nothing(Maybe[T]):
    def bind(self, func: Callable[[T], 'Monad[U]']) -> 'Monad[U]':
        return self
        
    def map(self, func: Callable[[T], U]) -> 'Monad[U]':
        return self

@dataclass
class Just(Maybe[T]):
    value: T
    
    def bind(self, func: Callable[[T], 'Monad[U]']) -> 'Monad[U]':
        return func(self.value)

# --- IO Monad (Side Effects) ---

class IO(Monad[T]):
    """Encapsulates a side-effecting computation."""
    
    def __init__(self, effect: Callable[[], T]):
        self._effect = effect
        
    def unsafe_run(self) -> T:
        """Execute the side effect."""
        return self._effect()
        
    def bind(self, func: Callable[[T], 'Monad[U]']) -> 'Monad[U]':
        def new_effect() -> U:
            value = self.unsafe_run()
            return func(value).unsafe_run()
        return IO(new_effect)

    @classmethod
    def pure(cls, value: T) -> 'IO[T]':
        return IO(lambda: value)

# --- Reader Monad (Dependency Injection) ---

class Reader(Monad[T], Generic[E, T]):
    """Computations which read from a shared environment."""
    
    def __init__(self, run: Callable[[E], T]):
        self.run = run
        
    def bind(self, func: Callable[[T], 'Reader[E, U]']) -> 'Reader[E, U]':
        def new_run(env: E) -> U:
            value = self.run(env)
            return func(value).run(env)
        return Reader(new_run)

    @classmethod
    def pure(cls, value: T) -> 'Reader[E, T]':
        return Reader(lambda _: value)
        
    @staticmethod
    def ask() -> 'Reader[E, E]':
        return Reader(lambda env: env)

# --- Writer Monad (Logging) ---

class Writer(Monad[T], Generic[L, T]):
    """Computations which produce a log side-effect."""
    
    def __init__(self, run: Callable[[], Tuple[T, List[L]]]):
        self.run = run
        
    def bind(self, func: Callable[[T], 'Writer[L, U]']) -> 'Writer[L, U]':
        def new_run() -> Tuple[U, List[L]]:
            val, log1 = self.run()
            result_writer = func(val)
            val2, log2 = result_writer.run()
            return val2, log1 + log2
        return Writer(new_run)

    @classmethod
    def pure(cls, value: T) -> 'Writer[L, T]':
        return Writer(lambda: (value, []))
        
    @staticmethod
    def tell(log: List[L]) -> 'Writer[L, None]':
        return Writer(lambda: (None, log))

# --- State Monad (State Management) ---

class State(Monad[T], Generic[E, T]):
    """Computations which carry a state."""
    
    def __init__(self, run: Callable[[E], Tuple[T, E]]):
        self.run = run
        
    def bind(self, func: Callable[[T], 'State[E, U]']) -> 'State[E, U]':
        def new_run(state: E) -> Tuple[U, E]:
            val, new_state = self.run(state)
            return func(val).run(new_state)
        return State(new_run)

    @classmethod
    def pure(cls, value: T) -> 'State[E, T]':
        return State(lambda s: (value, s))
        
    @staticmethod
    def get() -> 'State[E, E]':
        return State(lambda s: (s, s))
        
    @staticmethod
    def put(new_state: E) -> 'State[E, None]':
        return State(lambda _: (None, new_state))
