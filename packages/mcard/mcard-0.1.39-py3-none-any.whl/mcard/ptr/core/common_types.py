"""
Common types and data structures for the PTR Core system.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, List, NewType, Tuple

# MCard as Prime Number (Atomic Identity)
PrimeHash = NewType('PrimeHash', str)

@dataclass
class PolynomialTerm:
    """
    Represents a term in the PCard Polynomial: A_i * X^{B_i}
    
    Where:
    - A_i (coefficient): Abstract Specification Hash (PrimeHash)
    - B_i (exponent): Balanced Expectation Hash (PrimeHash)
    - X: The Operator/Function being evaluated
    """
    coefficient: PrimeHash  # Abstract Spec
    exponent: PrimeHash     # Balanced Expectation
    weight: float = 1.0     # Optional weighting for semantic embedding


@dataclass
class SafetyViolation:
    """Records safety property violations"""
    property: str
    violation_type: str
    details: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class LivenessMetric:
    """Tracks liveness properties (progress toward goals)"""
    goal: str
    progress: float  # 0.0 to 1.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class VerificationStatus(Enum):
    """Status of CLM verification tracking temporal progression"""
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ExecutionResult:
    """Result of a PCard execution with correctness measures
    
    Implements Computable Certificate pattern:
    - success/output: Generator's complex computation result
    - verification_vcard: Certificate (immutable audit evidence)
    - alignment_score: Directional alignment measure (cosine similarity)
    - invariants_preserved: Jacobian check (transformation verifiability)
    """
    success: bool
    output: Any
    verification_vcard: Optional[str]  # Hash of the verification VCard
    execution_time_ms: int
    
    # Correctness Measures (from MVP+CLM Integration)
    alignment_score: Optional[float] = None  # cos(actual, spec) - should be ≥ 0.85
    invariants_preserved: bool = True  # |J| ≠ 0 check
    
    # Safety and Liveness Tracking
    safety_violations: List[SafetyViolation] = field(default_factory=list)
    liveness_metrics: List[LivenessMetric] = field(default_factory=list)
    
    error_message: Optional[str] = None
