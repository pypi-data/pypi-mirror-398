"""
Beta Reduction - Function application in Lambda Calculus

Beta reduction (β-reduction) is the computational rule:
  (λx.M) N →β M[x:=N]

This module provides:
- Single-step beta reduction
- Full normalization with multiple strategies
- Capture-avoiding substitution
- Redex detection and search

This module provides Python parity with mcard-js/src/ptr/lambda/BetaReduction.ts
"""

from typing import Optional, List, Literal, NamedTuple
from dataclasses import dataclass

from mcard.model.card_collection import CardCollection
from mcard.ptr.lambda_calc.lambda_term import (
    LambdaTerm, VarTerm, AbsTerm, AppTerm,
    mk_var, mk_abs, mk_app,
    load_term, store_term, is_var, is_abs, is_app
)
from mcard.ptr.lambda_calc.free_variables import (
    free_variables, is_free_in, generate_fresh_for
)
from mcard.ptr.lambda_calc.alpha_conversion import alpha_rename


# ─────────────────────────────────────────────────────────────────────────────
# Types
# ─────────────────────────────────────────────────────────────────────────────

ReductionStrategy = Literal['normal', 'applicative', 'lazy']


@dataclass
class NormalizationResult:
    """Result of normalization"""
    normal_form: str       # Hash of the normal form
    steps: int             # Number of reduction steps
    reduction_path: List[str]  # Hashes of intermediate forms


# ─────────────────────────────────────────────────────────────────────────────
# Substitution with Capture Avoidance
# ─────────────────────────────────────────────────────────────────────────────

def substitute_with_capture(
    collection: CardCollection,
    term_hash: str,
    var_name: str,
    replacement_hash: str
) -> Optional[str]:
    """
    Perform capture-avoiding substitution: M[x:=N]
    
    This is the core operation that replaces all free occurrences of x in M with N,
    while avoiding variable capture by renaming bound variables as needed.
    """
    term = load_term(collection, term_hash)
    if term is None:
        return None
    
    if is_var(term):
        if term.name == var_name:
            return replacement_hash
        return term_hash
    
    elif is_abs(term):
        if term.param == var_name:
            # x is bound here - no substitution in body
            return term_hash
        
        # Check for capture: if param is free in replacement
        param_free_in_repl = is_free_in(collection, term.param, replacement_hash)
        if param_free_in_repl is None:
            return None
        
        if param_free_in_repl:
            # Need to alpha-rename to avoid capture
            fresh = generate_fresh_for(collection, term.param, term.body, replacement_hash)
            renamed_body = alpha_rename(collection, term.body, term.param, fresh)
            if renamed_body is None:
                return None
            
            new_body = substitute_with_capture(collection, renamed_body, var_name, replacement_hash)
            if new_body is None:
                return None
            
            return store_term(collection, mk_abs(fresh, new_body))
        
        # Safe to substitute directly
        new_body = substitute_with_capture(collection, term.body, var_name, replacement_hash)
        if new_body is None:
            return None
        
        return store_term(collection, mk_abs(term.param, new_body))
    
    elif is_app(term):
        new_func = substitute_with_capture(collection, term.func, var_name, replacement_hash)
        new_arg = substitute_with_capture(collection, term.arg, var_name, replacement_hash)
        if new_func is None or new_arg is None:
            return None
        return store_term(collection, mk_app(new_func, new_arg))
    
    return term_hash


# ─────────────────────────────────────────────────────────────────────────────
# Redex Detection
# ─────────────────────────────────────────────────────────────────────────────

def is_redex(collection: CardCollection, hash_value: str) -> Optional[bool]:
    """
    Check if a term is a beta-redex: (λx.M) N
    """
    term = load_term(collection, hash_value)
    if term is None:
        return None
    
    if is_app(term):
        func = load_term(collection, term.func)
        if func is not None and is_abs(func):
            return True
    
    return False


def find_leftmost_redex(
    collection: CardCollection,
    hash_value: str
) -> Optional[str]:
    """
    Find the leftmost-outermost beta-redex (normal order).
    Returns the hash of the redex, or None if none found.
    """
    term = load_term(collection, hash_value)
    if term is None:
        return None
    
    if is_app(term):
        # Check if this is a redex
        func = load_term(collection, term.func)
        if func is not None and is_abs(func):
            return hash_value
        
        # Try left subtree first
        left_redex = find_leftmost_redex(collection, term.func)
        if left_redex:
            return left_redex
        
        # Then right subtree
        return find_leftmost_redex(collection, term.arg)
    
    elif is_abs(term):
        return find_leftmost_redex(collection, term.body)
    
    return None


def find_innermost_redex(
    collection: CardCollection,
    hash_value: str
) -> Optional[str]:
    """
    Find the innermost-leftmost beta-redex (applicative order).
    Returns the hash of the redex, or None if none found.
    """
    term = load_term(collection, hash_value)
    if term is None:
        return None
    
    if is_app(term):
        # Try subtrees first
        left_redex = find_innermost_redex(collection, term.func)
        if left_redex:
            return left_redex
        
        right_redex = find_innermost_redex(collection, term.arg)
        if right_redex:
            return right_redex
        
        # Check if this is a redex
        func = load_term(collection, term.func)
        if func is not None and is_abs(func):
            return hash_value
    
    elif is_abs(term):
        return find_innermost_redex(collection, term.body)
    
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Beta Reduction
# ─────────────────────────────────────────────────────────────────────────────

def beta_reduce(collection: CardCollection, hash_value: str) -> Optional[str]:
    """
    Perform a single beta reduction step on a redex.
    
    (λx.M) N →β M[x:=N]
    
    Returns the hash of the reduced term, or None if not a redex.
    """
    term = load_term(collection, hash_value)
    if term is None:
        return None
    
    if not is_app(term):
        return None
    
    func = load_term(collection, term.func)
    if func is None or not is_abs(func):
        return None
    
    # Perform substitution: body[param:=arg]
    return substitute_with_capture(collection, func.body, func.param, term.arg)


def reduce_step(
    collection: CardCollection,
    hash_value: str,
    strategy: ReductionStrategy = 'normal'
) -> Optional[str]:
    """
    Perform a single reduction step using the specified strategy.
    Returns None if no reduction is possible.
    """
    term = load_term(collection, hash_value)
    if term is None:
        return None
    
    # Find redex based on strategy
    if strategy == 'normal':
        redex_hash = find_leftmost_redex(collection, hash_value)
    elif strategy == 'applicative':
        redex_hash = find_innermost_redex(collection, hash_value)
    else:  # lazy
        redex_hash = find_leftmost_redex(collection, hash_value)
    
    if not redex_hash:
        return None
    
    # Reduce the redex
    reduced = beta_reduce(collection, redex_hash)
    if reduced is None:
        return None
    
    # Replace the redex in the original term
    return replace_subterm(collection, hash_value, redex_hash, reduced)


def replace_subterm(
    collection: CardCollection,
    term_hash: str,
    target_hash: str,
    replacement_hash: str
) -> Optional[str]:
    """
    Replace a subterm (identified by hash) with another term.
    """
    if term_hash == target_hash:
        return replacement_hash
    
    term = load_term(collection, term_hash)
    if term is None:
        return None
    
    if is_var(term):
        return term_hash
    
    elif is_abs(term):
        new_body = replace_subterm(collection, term.body, target_hash, replacement_hash)
        if new_body is None:
            return None
        if new_body == term.body:
            return term_hash
        return store_term(collection, mk_abs(term.param, new_body))
    
    elif is_app(term):
        new_func = replace_subterm(collection, term.func, target_hash, replacement_hash)
        new_arg = replace_subterm(collection, term.arg, target_hash, replacement_hash)
        if new_func is None or new_arg is None:
            return None
        if new_func == term.func and new_arg == term.arg:
            return term_hash
        return store_term(collection, mk_app(new_func, new_arg))
    
    return term_hash


# ─────────────────────────────────────────────────────────────────────────────
# Normalization
# ─────────────────────────────────────────────────────────────────────────────

def normalize(
    collection: CardCollection,
    hash_value: str,
    strategy: ReductionStrategy = 'normal',
    max_steps: int = 1000
) -> Optional[NormalizationResult]:
    """
    Normalize a Lambda term by repeatedly applying reduction steps.
    
    Returns the normal form if found within max_steps, or None if:
    - Term not found
    - Reduction diverges (exceeds max_steps)
    """
    current = hash_value
    path = [current]
    steps = 0
    
    while steps < max_steps:
        next_term = reduce_step(collection, current, strategy)
        
        if next_term is None:
            # No more reductions - we're in normal form
            return NormalizationResult(
                normal_form=current,
                steps=steps,
                reduction_path=path
            )
        
        steps += 1
        current = next_term
        path.append(current)
    
    # Exceeded max steps - possibly divergent
    return None


def is_normal_form(collection: CardCollection, hash_value: str) -> Optional[bool]:
    """Check if a term is in normal form (contains no redexes)"""
    redex = find_leftmost_redex(collection, hash_value)
    return redex is None


def has_normal_form(
    collection: CardCollection,
    hash_value: str,
    max_steps: int = 1000
) -> Optional[bool]:
    """Check if a term has a normal form (within max_steps)"""
    result = normalize(collection, hash_value, 'normal', max_steps)
    return result is not None
