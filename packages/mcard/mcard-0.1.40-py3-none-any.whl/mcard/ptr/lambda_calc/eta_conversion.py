"""
Eta Conversion - Extensional equality in Lambda Calculus

Eta conversion (η-conversion) captures extensional equivalence:
  λx.(M x) ≡η M  (when x is not free in M)

This expresses that two functions are equal if they produce the same
result for all inputs.

This module provides Python parity with mcard-js/src/ptr/lambda/EtaConversion.ts
"""

from typing import Optional

from mcard.model.card_collection import CardCollection
from mcard.ptr.lambda_calc.lambda_term import (
    LambdaTerm, VarTerm, AbsTerm, AppTerm,
    mk_var, mk_abs, mk_app,
    load_term, store_term, is_var, is_abs, is_app
)
from mcard.ptr.lambda_calc.free_variables import (
    is_free_in, generate_fresh_for
)
from mcard.ptr.lambda_calc.alpha_conversion import alpha_equivalent


# ─────────────────────────────────────────────────────────────────────────────
# Eta Reduction
# ─────────────────────────────────────────────────────────────────────────────

def eta_reduce(collection: CardCollection, hash_value: str) -> Optional[str]:
    """
    Perform eta reduction on a term.
    
    λx.(M x) →η M  (when x is not free in M)
    
    Returns the reduced term hash, or the original if not reducible.
    """
    term = load_term(collection, hash_value)
    if term is None:
        return None
    
    if is_abs(term):
        # Check if body is application
        body = load_term(collection, term.body)
        if body is None:
            return None
        
        if is_app(body):
            # Check if arg is the bound variable
            arg = load_term(collection, body.arg)
            if arg is None:
                return None
            
            if is_var(arg) and arg.name == term.param:
                # Check if param is NOT free in func
                free_check = is_free_in(collection, term.param, body.func)
                if free_check is not None and not free_check:
                    # η-reduction applies!
                    return body.func
    
    # No reduction possible at top level, try subterms
    if is_abs(term):
        new_body = eta_reduce(collection, term.body)
        if new_body is None:
            return None
        if new_body != term.body:
            return store_term(collection, mk_abs(term.param, new_body))
        return hash_value
    
    elif is_app(term):
        new_func = eta_reduce(collection, term.func)
        new_arg = eta_reduce(collection, term.arg)
        if new_func is None or new_arg is None:
            return None
        if new_func != term.func or new_arg != term.arg:
            return store_term(collection, mk_app(new_func, new_arg))
        return hash_value
    
    return hash_value


# ─────────────────────────────────────────────────────────────────────────────
# Eta Expansion
# ─────────────────────────────────────────────────────────────────────────────

def eta_expand(
    collection: CardCollection,
    hash_value: str,
    fresh_var: Optional[str] = None
) -> Optional[str]:
    """
    Perform eta expansion on a term.
    
    M →η λx.(M x)  (where x is fresh)
    
    Returns the expanded term hash.
    """
    term = load_term(collection, hash_value)
    if term is None:
        return None
    
    # Generate fresh variable if not provided
    if fresh_var is None:
        fresh_var = generate_fresh_for(collection, 'η', hash_value)
    
    # Create variable term
    var_hash = store_term(collection, mk_var(fresh_var))
    
    # Create application: M x
    app_hash = store_term(collection, mk_app(hash_value, var_hash))
    
    # Create abstraction: λx.(M x)
    return store_term(collection, mk_abs(fresh_var, app_hash))


# ─────────────────────────────────────────────────────────────────────────────
# Eta Equivalence
# ─────────────────────────────────────────────────────────────────────────────

def eta_equivalent(
    collection: CardCollection,
    hash1: str,
    hash2: str
) -> Optional[bool]:
    """
    Check if two terms are η-equivalent.
    
    Performs full η-reduction on both terms and checks α-equivalence.
    """
    # Fully eta-reduce both terms
    reduced1 = fully_eta_reduce(collection, hash1)
    reduced2 = fully_eta_reduce(collection, hash2)
    
    if reduced1 is None or reduced2 is None:
        return None
    
    # Check alpha equivalence
    return alpha_equivalent(collection, reduced1, reduced2)


def fully_eta_reduce(
    collection: CardCollection,
    hash_value: str,
    max_steps: int = 100
) -> Optional[str]:
    """
    Repeatedly apply eta reduction until no more reductions apply.
    """
    current = hash_value
    steps = 0
    
    while steps < max_steps:
        reduced = eta_reduce(collection, current)
        if reduced is None:
            return None
        
        if reduced == current:
            # No more reductions
            return current
        
        current = reduced
        steps += 1
    
    return current


# ─────────────────────────────────────────────────────────────────────────────
# Combined Beta-Eta Reduction
# ─────────────────────────────────────────────────────────────────────────────

def beta_eta_reduce(
    collection: CardCollection,
    hash_value: str
) -> Optional[str]:
    """
    Perform one step of beta or eta reduction.
    Tries beta first, then eta.
    """
    from mcard.ptr.lambda_calc.beta_reduction import reduce_step
    
    # Try beta reduction first
    beta_result = reduce_step(collection, hash_value, 'normal')
    if beta_result is not None:
        return beta_result
    
    # Try eta reduction
    eta_result = eta_reduce(collection, hash_value)
    if eta_result is not None and eta_result != hash_value:
        return eta_result
    
    return None


def beta_eta_normalize(
    collection: CardCollection,
    hash_value: str,
    max_steps: int = 1000
) -> Optional[str]:
    """
    Normalize a term using both beta and eta reductions.
    """
    current = hash_value
    steps = 0
    
    while steps < max_steps:
        reduced = beta_eta_reduce(collection, current)
        if reduced is None:
            return current
        
        current = reduced
        steps += 1
    
    return None
