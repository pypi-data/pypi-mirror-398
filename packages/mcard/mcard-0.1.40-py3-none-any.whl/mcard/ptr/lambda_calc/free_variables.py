"""
Free Variables - Analysis of free and bound variables in Lambda terms

Provides utilities for computing free variables, bound variables,
and checking if variables are captured during substitution.

This module provides Python parity with mcard-js/src/ptr/lambda/FreeVariables.ts
"""

from typing import Set, Optional
import itertools

from mcard.model.card_collection import CardCollection
from mcard.ptr.lambda_calc.lambda_term import (
    LambdaTerm, VarTerm, AbsTerm, AppTerm,
    load_term, is_var, is_abs, is_app
)


# ─────────────────────────────────────────────────────────────────────────────
# Free Variables
# ─────────────────────────────────────────────────────────────────────────────

def free_variables(collection: CardCollection, hash_value: str) -> Optional[Set[str]]:
    """
    Compute the set of free variables in a Lambda term.
    
    FV(x) = {x}
    FV(λx.M) = FV(M) - {x}
    FV(M N) = FV(M) ∪ FV(N)
    """
    term = load_term(collection, hash_value)
    if term is None:
        return None
    
    if is_var(term):
        return {term.name}
    
    elif is_abs(term):
        body_fv = free_variables(collection, term.body)
        if body_fv is None:
            return None
        return body_fv - {term.param}
    
    elif is_app(term):
        func_fv = free_variables(collection, term.func)
        arg_fv = free_variables(collection, term.arg)
        if func_fv is None or arg_fv is None:
            return None
        return func_fv | arg_fv
    
    return set()


# ─────────────────────────────────────────────────────────────────────────────
# Bound Variables
# ─────────────────────────────────────────────────────────────────────────────

def bound_variables(collection: CardCollection, hash_value: str) -> Optional[Set[str]]:
    """
    Compute the set of bound variables in a Lambda term.
    
    BV(x) = {}
    BV(λx.M) = BV(M) ∪ {x}
    BV(M N) = BV(M) ∪ BV(N)
    """
    term = load_term(collection, hash_value)
    if term is None:
        return None
    
    if is_var(term):
        return set()
    
    elif is_abs(term):
        body_bv = bound_variables(collection, term.body)
        if body_bv is None:
            return None
        return body_bv | {term.param}
    
    elif is_app(term):
        func_bv = bound_variables(collection, term.func)
        arg_bv = bound_variables(collection, term.arg)
        if func_bv is None or arg_bv is None:
            return None
        return func_bv | arg_bv
    
    return set()


# ─────────────────────────────────────────────────────────────────────────────
# Variable Checks
# ─────────────────────────────────────────────────────────────────────────────

def is_free_in(collection: CardCollection, var_name: str, hash_value: str) -> Optional[bool]:
    """Check if a variable is free in a term"""
    fv = free_variables(collection, hash_value)
    if fv is None:
        return None
    return var_name in fv


def is_closed(collection: CardCollection, hash_value: str) -> Optional[bool]:
    """Check if a term is closed (has no free variables)"""
    fv = free_variables(collection, hash_value)
    if fv is None:
        return None
    return len(fv) == 0


# ─────────────────────────────────────────────────────────────────────────────
# Fresh Name Generation
# ─────────────────────────────────────────────────────────────────────────────

def generate_fresh(base: str, avoid: Set[str]) -> str:
    """
    Generate a fresh variable name that doesn't conflict with avoid set.
    Uses primes: x, x', x'', x'''...
    """
    candidate = base
    while candidate in avoid:
        candidate = candidate + "'"
    return candidate


def generate_fresh_for(
    collection: CardCollection,
    base: str,
    *hashes: str
) -> str:
    """
    Generate a fresh variable name avoiding all variables in the given terms.
    """
    avoid: Set[str] = set()
    
    for h in hashes:
        fv = free_variables(collection, h)
        if fv:
            avoid |= fv
        bv = bound_variables(collection, h)
        if bv:
            avoid |= bv
    
    return generate_fresh(base, avoid)


# ─────────────────────────────────────────────────────────────────────────────
# Set Operations
# ─────────────────────────────────────────────────────────────────────────────

def set_difference(a: Set[str], b: Set[str]) -> Set[str]:
    """Set difference: A - B"""
    return a - b


def set_intersection(a: Set[str], b: Set[str]) -> Set[str]:
    """Set intersection: A ∩ B"""
    return a & b


def set_union(a: Set[str], b: Set[str]) -> Set[str]:
    """Set union: A ∪ B"""
    return a | b
