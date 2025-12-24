"""
Polynomial Operator - The Algebra of Composition for PCards

This module implements the PCard as a Polynomial Operator, realizing the
theoretical foundation of "The Algebra of Composition".

PCard = Operator (Function)
Structure = Sum(A_i * X^{B_i})
"""

from dataclasses import dataclass, field
from typing import List, Optional

from mcard.ptr.core.common_types import PrimeHash, PolynomialTerm


@dataclass
class PolynomialStructure:
    """
    Represents the polynomial structure of a PCard.
    
    F(X) = Sum(A_i * X^{B_i}) + C
    
    Where:
    - A_i: Abstract Specifications (Coefficients)
    - B_i: Balanced Expectations (Exponents)
    - C: Concrete Implementation (Constant/Base)
    """
    terms: List[PolynomialTerm] = field(default_factory=list)
    constant: Optional[PrimeHash] = None  # Concrete Implementation Hash
    
    def add_term(self, abstract_hash: str, balanced_hash: str) -> None:
        """Add a term (A * X^B) to the polynomial."""
        self.terms.append(PolynomialTerm(
            coefficient=PrimeHash(abstract_hash),
            exponent=PrimeHash(balanced_hash)
        ))
        
    def set_constant(self, concrete_hash: str) -> None:
        """Set the constant term (C) - the Concrete Implementation."""
        self.constant = PrimeHash(concrete_hash)
        
    def compose(self, other: 'PolynomialStructure') -> 'PolynomialStructure':
        """
        Compose this polynomial with another: (F * G)(X)
        
        Implements Dirichlet Convolution logic for composition.
        """
        # Simplified composition logic for now:
        # Merges terms and updates constant if compatible
        new_poly = PolynomialStructure()
        new_poly.terms.extend(self.terms)
        new_poly.terms.extend(other.terms)
        
        # In a real convolution, we'd have more complex logic for combining constants
        # For now, we take the 'other' constant as the new base if present
        new_poly.constant = other.constant or self.constant
        
        return new_poly

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "terms": [
                {
                    "coefficient": str(t.coefficient),
                    "exponent": str(t.exponent),
                    "weight": t.weight
                }
                for t in self.terms
            ],
            "constant": str(self.constant) if self.constant else None
        }
