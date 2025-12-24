"""
Lambda Calculus Module for Python MCard

Provides α-β-η conversions on MCard-stored Lambda terms.

This module provides Python parity with mcard-js/src/ptr/lambda/
"""

# Lambda Term ADT
from mcard.ptr.lambda_calc.lambda_term import (
    LambdaTerm,
    VarTerm,
    AbsTerm,
    AppTerm,
    mk_var,
    mk_abs,
    mk_app,
    serialize_term,
    deserialize_term,
    term_to_mcard,
    mcard_to_term,
    store_term,
    load_term,
    term_exists,
    pretty_print_shallow,
    pretty_print_deep,
    is_var,
    is_abs,
    is_app,
)

# Free Variables
from mcard.ptr.lambda_calc.free_variables import (
    free_variables,
    bound_variables,
    is_free_in,
    is_closed,
    generate_fresh,
    generate_fresh_for,
)

# Alpha Conversion
from mcard.ptr.lambda_calc.alpha_conversion import (
    alpha_rename,
    alpha_equivalent,
    alpha_normalize,
)

# Beta Reduction
from mcard.ptr.lambda_calc.beta_reduction import (
    ReductionStrategy,
    NormalizationResult,
    substitute_with_capture,
    is_redex,
    find_leftmost_redex,
    find_innermost_redex,
    beta_reduce,
    reduce_step,
    normalize,
    is_normal_form,
    has_normal_form,
)

# Eta Conversion
from mcard.ptr.lambda_calc.eta_conversion import (
    eta_reduce,
    eta_expand,
    eta_equivalent,
    fully_eta_reduce,
    beta_eta_reduce,
    beta_eta_normalize,
)

# Lambda Runtime
from mcard.ptr.lambda_calc.lambda_runtime import (
    parse_lambda_expression,
    ParseError,
    LambdaParser,
    LambdaOperation,
    LambdaConfig,
    LambdaRuntimeResult,
    LambdaRuntime,
)


__all__ = [
    # Lambda Term ADT
    'LambdaTerm',
    'VarTerm',
    'AbsTerm',
    'AppTerm',
    'mk_var',
    'mk_abs',
    'mk_app',
    'serialize_term',
    'deserialize_term',
    'term_to_mcard',
    'mcard_to_term',
    'store_term',
    'load_term',
    'term_exists',
    'pretty_print_shallow',
    'pretty_print_deep',
    'is_var',
    'is_abs',
    'is_app',
    # Free Variables
    'free_variables',
    'bound_variables',
    'is_free_in',
    'is_closed',
    'generate_fresh',
    'generate_fresh_for',
    # Alpha Conversion
    'alpha_rename',
    'alpha_equivalent',
    'alpha_normalize',
    # Beta Reduction
    'ReductionStrategy',
    'NormalizationResult',
    'substitute_with_capture',
    'is_redex',
    'find_leftmost_redex',
    'find_innermost_redex',
    'beta_reduce',
    'reduce_step',
    'normalize',
    'is_normal_form',
    'has_normal_form',
    # Eta Conversion
    'eta_reduce',
    'eta_expand',
    'eta_equivalent',
    'fully_eta_reduce',
    'beta_eta_reduce',
    'beta_eta_normalize',
    # Lambda Runtime
    'parse_lambda_expression',
    'ParseError',
    'LambdaParser',
    'LambdaOperation',
    'LambdaConfig',
    'LambdaRuntimeResult',
    'LambdaRuntime',
]
