"""
Alpha Conversion - Variable renaming in Lambda Calculus

Alpha conversion (α-conversion) allows renaming of bound variables
without changing the meaning of the term:
  λx.M ≡α λy.M[x:=y]  (where y is fresh)

This module provides Python parity with mcard-js/src/ptr/lambda/AlphaConversion.ts
"""

from typing import Optional, Dict

from mcard.model.card_collection import CardCollection
from mcard.ptr.lambda_calc.lambda_term import (
    LambdaTerm, VarTerm, AbsTerm, AppTerm,
    mk_var, mk_abs, mk_app,
    load_term, store_term, is_var, is_abs, is_app
)
from mcard.ptr.lambda_calc.free_variables import (
    free_variables, bound_variables, generate_fresh_for
)


# ─────────────────────────────────────────────────────────────────────────────
# Alpha Renaming
# ─────────────────────────────────────────────────────────────────────────────

def alpha_rename(
    collection: CardCollection,
    hash_value: str,
    old_name: str,
    new_name: str
) -> Optional[str]:
    """
    Rename a bound variable in a Lambda term.
    Returns the hash of the renamed term, or None if term not found.
    
    Only renames the binding occurrence and all bound occurrences.
    """
    term = load_term(collection, hash_value)
    if term is None:
        return None
    
    if is_var(term):
        # Variable: rename if it matches
        if term.name == old_name:
            return store_term(collection, mk_var(new_name))
        return hash_value
    
    elif is_abs(term):
        if term.param == old_name:
            # This is the binder we're renaming
            new_body = alpha_rename(collection, term.body, old_name, new_name)
            if new_body is None:
                return None
            return store_term(collection, mk_abs(new_name, new_body))
        else:
            # Not bound here, recurse into body
            new_body = alpha_rename(collection, term.body, old_name, new_name)
            if new_body is None:
                return None
            return store_term(collection, mk_abs(term.param, new_body))
    
    elif is_app(term):
        new_func = alpha_rename(collection, term.func, old_name, new_name)
        new_arg = alpha_rename(collection, term.arg, old_name, new_name)
        if new_func is None or new_arg is None:
            return None
        return store_term(collection, mk_app(new_func, new_arg))
    
    return hash_value


# ─────────────────────────────────────────────────────────────────────────────
# Alpha Equivalence
# ─────────────────────────────────────────────────────────────────────────────

def alpha_equivalent(
    collection: CardCollection,
    hash1: str,
    hash2: str,
    env: Optional[Dict[str, str]] = None
) -> Optional[bool]:
    """
    Check if two Lambda terms are α-equivalent.
    
    Two terms are α-equivalent if they differ only in the names of bound variables.
    Uses a bijection to track corresponding bound variable names.
    """
    if env is None:
        env = {}
    
    term1 = load_term(collection, hash1)
    term2 = load_term(collection, hash2)
    
    if term1 is None or term2 is None:
        return None
    
    if is_var(term1) and is_var(term2):
        # Check if variables correspond via environment
        mapped = env.get(term1.name)
        if mapped is not None:
            return mapped == term2.name
        # Not bound - must be same free variable
        return term1.name == term2.name
    
    elif is_abs(term1) and is_abs(term2):
        # Extend environment with parameter correspondence
        new_env = dict(env)
        new_env[term1.param] = term2.param
        return alpha_equivalent(collection, term1.body, term2.body, new_env)
    
    elif is_app(term1) and is_app(term2):
        func_eq = alpha_equivalent(collection, term1.func, term2.func, env)
        if not func_eq:
            return func_eq
        return alpha_equivalent(collection, term1.arg, term2.arg, env)
    
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Alpha Normalization
# ─────────────────────────────────────────────────────────────────────────────

def alpha_normalize(
    collection: CardCollection,
    hash_value: str,
    counter: Optional[list] = None
) -> Optional[str]:
    """
    Normalize bound variable names using de Bruijn-style naming.
    
    All bound variables are renamed to x0, x1, x2, etc. in order of binding.
    This produces a canonical form for α-equivalent terms.
    """
    if counter is None:
        counter = [0]
    
    term = load_term(collection, hash_value)
    if term is None:
        return None
    
    if is_var(term):
        return hash_value
    
    elif is_abs(term):
        # Generate fresh normalized name
        new_name = f"x{counter[0]}"
        counter[0] += 1
        
        # Rename this binding
        renamed_body = alpha_rename(collection, term.body, term.param, new_name)
        if renamed_body is None:
            return None
        
        # Recursively normalize the body
        normalized_body = alpha_normalize(collection, renamed_body, counter)
        if normalized_body is None:
            return None
        
        return store_term(collection, mk_abs(new_name, normalized_body))
    
    elif is_app(term):
        norm_func = alpha_normalize(collection, term.func, counter)
        norm_arg = alpha_normalize(collection, term.arg, counter)
        if norm_func is None or norm_arg is None:
            return None
        return store_term(collection, mk_app(norm_func, norm_arg))
    
    return hash_value
