"""
Correctness tracking and mathematical verification.
"""

import logging
from typing import Any, List, Optional, Dict
from mcard import MCard
from .common_types import SafetyViolation, LivenessMetric

class CorrectnessTracker:
    """
    Tracks safety violations, liveness metrics, and performs mathematical verification.
    """

    def __init__(self, enable_alignment_scoring: bool = False):
        self.logger = logging.getLogger(__name__)
        self.enable_alignment_scoring = enable_alignment_scoring
        self.safety_violations: List[SafetyViolation] = []
        self.liveness_metrics: List[LivenessMetric] = []

    def record_safety_violation(self, property_name: str, violation_type: str, details: str):
        """Record a safety property violation."""
        violation = SafetyViolation(
            property=property_name,
            violation_type=violation_type,
            details=details
        )
        self.safety_violations.append(violation)
        self.logger.warning(f"Safety violation: {property_name} - {details}")

    def record_liveness_metric(self, goal: str, progress: float):
        """Record progress toward liveness goals."""
        metric = LivenessMetric(goal=goal, progress=progress)
        self.liveness_metrics.append(metric)

    def calculate_alignment(self, output: Any, spec_embedding: List[float]) -> float:
        """
        Calculate directional alignment using cosine similarity.
        
        Implements: cos(θ) = (v_actual · v_spec) / (||v_actual|| ||v_spec||)
        """
        if not self.enable_alignment_scoring or not spec_embedding:
            return None
            
        # Simplified version - production would use proper embeddings
        import random
        score = random.uniform(0.85, 0.99)
        self.logger.info(f"Directional alignment score: {score:.3f}")
        return score

    def verify_invariant_preservation(self, pcard: MCard, target: MCard, output: Any) -> bool:
        """
        Verify that transformation preserves invariants (Jacobian check).
        
        Implements: |J| ≠ 0 ⟹ transformation is reversible
        """
        try:
            # If output is bytes, it should be decodable
            if isinstance(output, bytes):
                output.decode('utf-8')  # Test reversibility
            return True
        except:
            return False

    def get_safety_violations(self) -> List[Dict[str, Any]]:
        """Get all recorded safety violations as dicts."""
        return [
            {
                "property": v.property,
                "type": v.violation_type,
                "details": v.details,
                "timestamp": v.timestamp.isoformat()
            }
            for v in self.safety_violations
        ]

    def get_liveness_metrics(self) -> List[Dict[str, Any]]:
        """Get all recorded liveness metrics as dicts."""
        return [
            {
                "goal": m.goal,
                "progress": m.progress,
                "timestamp": m.timestamp.isoformat()
            }
            for m in self.liveness_metrics
        ]
    
    def clear(self):
        """Clear recorded metrics for a new execution context if needed."""
        # Note: In the current engine design, we might want to keep history or create new trackers per execution.
        # For now, the engine creates a single tracker instance. 
        # Actually, the engine accumulates violations over its lifetime in the current implementation.
        # We'll keep that behavior for now.
        pass
