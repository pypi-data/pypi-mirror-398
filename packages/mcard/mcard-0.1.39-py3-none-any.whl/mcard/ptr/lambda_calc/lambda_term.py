"""
Lambda Term - Algebraic Data Type for Lambda Calculus

Represents Lambda Calculus terms as content-addressable MCards.
Each term variant is stored as JSON in MCard content, with sub-terms
referenced by their SHA-256 hashes for structural sharing.

The three term constructors mirror the BNF grammar:
  M, N ::= x | λx.M | M N

This module provides Python parity with mcard-js/src/ptr/lambda/LambdaTerm.ts
"""

from dataclasses import dataclass
from typing import Union, Optional, Literal
import json

from mcard.model.card import MCard
from mcard.model.card_collection import CardCollection


# ─────────────────────────────────────────────────────────────────────────────
# Lambda Term ADT
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class VarTerm:
    """Variable term: x"""
    tag: Literal['Var'] = 'Var'
    name: str = ''
    
    def __init__(self, name: str):
        object.__setattr__(self, 'name', name)
        object.__setattr__(self, 'tag', 'Var')


@dataclass(frozen=True)
class AbsTerm:
    """Abstraction term: λx.M - Body is stored as MCard hash"""
    tag: Literal['Abs'] = 'Abs'
    param: str = ''
    body: str = ''  # MCard hash of body term
    
    def __init__(self, param: str, body: str):
        object.__setattr__(self, 'param', param)
        object.__setattr__(self, 'body', body)
        object.__setattr__(self, 'tag', 'Abs')


@dataclass(frozen=True)
class AppTerm:
    """Application term: M N - Both func and arg are MCard hashes"""
    tag: Literal['App'] = 'App'
    func: str = ''  # MCard hash of function
    arg: str = ''   # MCard hash of argument
    
    def __init__(self, func: str, arg: str):
        object.__setattr__(self, 'func', func)
        object.__setattr__(self, 'arg', arg)
        object.__setattr__(self, 'tag', 'App')


LambdaTerm = Union[VarTerm, AbsTerm, AppTerm]


# ─────────────────────────────────────────────────────────────────────────────
# Constructors (Smart Constructors)
# ─────────────────────────────────────────────────────────────────────────────

def mk_var(name: str) -> VarTerm:
    """Create a variable term"""
    return VarTerm(name=name)


def mk_abs(param: str, body_hash: str) -> AbsTerm:
    """Create an abstraction term"""
    return AbsTerm(param=param, body=body_hash)


def mk_app(func_hash: str, arg_hash: str) -> AppTerm:
    """Create an application term"""
    return AppTerm(func=func_hash, arg=arg_hash)


# ─────────────────────────────────────────────────────────────────────────────
# Serialization
# ─────────────────────────────────────────────────────────────────────────────

def serialize_term(term: LambdaTerm) -> str:
    """Serialize a Lambda term to MCard content (JSON string)"""
    if isinstance(term, VarTerm):
        return json.dumps({'tag': 'Var', 'name': term.name})
    elif isinstance(term, AbsTerm):
        return json.dumps({'tag': 'Abs', 'param': term.param, 'body': term.body})
    elif isinstance(term, AppTerm):
        return json.dumps({'tag': 'App', 'func': term.func, 'arg': term.arg})
    else:
        raise ValueError(f"Unknown term type: {type(term)}")


def deserialize_term(content: str) -> LambdaTerm:
    """Deserialize MCard content to Lambda term"""
    parsed = json.loads(content)
    
    if not parsed.get('tag'):
        raise ValueError('Invalid Lambda term: missing tag')
    
    tag = parsed['tag']
    
    if tag == 'Var':
        if not isinstance(parsed.get('name'), str):
            raise ValueError('Invalid Var term: name must be string')
        return mk_var(parsed['name'])
    
    elif tag == 'Abs':
        if not isinstance(parsed.get('param'), str) or not isinstance(parsed.get('body'), str):
            raise ValueError('Invalid Abs term: param and body must be strings')
        return mk_abs(parsed['param'], parsed['body'])
    
    elif tag == 'App':
        if not isinstance(parsed.get('func'), str) or not isinstance(parsed.get('arg'), str):
            raise ValueError('Invalid App term: func and arg must be strings')
        return mk_app(parsed['func'], parsed['arg'])
    
    else:
        raise ValueError(f"Unknown Lambda term tag: {tag}")


def term_to_mcard(term: LambdaTerm) -> MCard:
    """Create an MCard from a Lambda term"""
    return MCard(content=serialize_term(term))


def mcard_to_term(mcard: MCard) -> LambdaTerm:
    """Extract Lambda term from MCard"""
    content = mcard.get_content(as_text=True)
    return deserialize_term(content)


# ─────────────────────────────────────────────────────────────────────────────
# Collection Operations
# ─────────────────────────────────────────────────────────────────────────────

def store_term(collection: CardCollection, term: LambdaTerm) -> str:
    """Store a Lambda term in the collection and return its hash"""
    mcard = term_to_mcard(term)
    collection.add(mcard)
    return mcard.hash


def load_term(collection: CardCollection, hash_value: str) -> Optional[LambdaTerm]:
    """Retrieve a Lambda term from the collection by hash"""
    mcard = collection.get(hash_value)
    if mcard is None:
        return None
    return mcard_to_term(mcard)


def term_exists(collection: CardCollection, hash_value: str) -> bool:
    """Check if a term exists in the collection"""
    return collection.get(hash_value) is not None


# ─────────────────────────────────────────────────────────────────────────────
# Pretty Printing
# ─────────────────────────────────────────────────────────────────────────────

def pretty_print_shallow(term: LambdaTerm) -> str:
    """Pretty-print a Lambda term (shallow - shows hashes for subterms)"""
    if isinstance(term, VarTerm):
        return term.name
    elif isinstance(term, AbsTerm):
        return f"λ{term.param}.〈{term.body[:8]}…〉"
    elif isinstance(term, AppTerm):
        return f"(〈{term.func[:8]}…〉 〈{term.arg[:8]}…〉)"
    else:
        return str(term)


def pretty_print_deep(collection: CardCollection, hash_value: str) -> str:
    """Pretty-print a Lambda term (deep - resolves all subterms from collection)"""
    term = load_term(collection, hash_value)
    if term is None:
        return f"〈missing:{hash_value[:8]}…〉"
    
    if isinstance(term, VarTerm):
        return term.name
    
    elif isinstance(term, AbsTerm):
        body = pretty_print_deep(collection, term.body)
        return f"(λ{term.param}.{body})"
    
    elif isinstance(term, AppTerm):
        func = pretty_print_deep(collection, term.func)
        arg = pretty_print_deep(collection, term.arg)
        return f"({func} {arg})"
    
    else:
        return str(term)


# ─────────────────────────────────────────────────────────────────────────────
# Type Guards
# ─────────────────────────────────────────────────────────────────────────────

def is_var(term: LambdaTerm) -> bool:
    """Check if term is a variable"""
    return isinstance(term, VarTerm)


def is_abs(term: LambdaTerm) -> bool:
    """Check if term is an abstraction"""
    return isinstance(term, AbsTerm)


def is_app(term: LambdaTerm) -> bool:
    """Check if term is an application"""
    return isinstance(term, AppTerm)
