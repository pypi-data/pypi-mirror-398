"""
Certificate generation for PTR execution evidence.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from mcard import MCard

class CertificateGenerator:
    """Generates VerificationVCards as computable certificates."""

    def __init__(self, collection):
        self.collection = collection
        self.logger = logging.getLogger(__name__)

    def generate_verification_vcard(
        self, 
        pcard_hash: str, 
        target_hash: str,
        verification_result, 
        execution_output: Any,
        alignment_score: Optional[float],
        invariants_preserved: bool
    ) -> str:
        """
        Generate VerificationVCard as computable certificate.
        
        This VCard provides:
        - Immutable audit evidence (content-addressed)
        - Cryptographic verification (hash-based)
        - Correctness measures (alignment, invariants)
        - Temporal provenance (timestamp)
        """
        vcard_content = {
            "type": "VerificationVCard",
            "subject": {
                "pcard_hash": pcard_hash,
                "target_hash": target_hash
            },
            "verifier": "ptr_engine_v0.2.0_correctness",
            "evidence": {
                "clm_verification": {
                    "abstract_valid": verification_result.abstract_valid,
                    "concrete_valid": verification_result.concrete_valid,
                    "balanced_valid": verification_result.balanced_valid,
                    "errors": verification_result.errors
                },
                "correctness_measures": {
                    "alignment_score": alignment_score,
                    "invariants_preserved": invariants_preserved,
                    "alignment_threshold": 0.85
                },
                "execution_output": str(execution_output),
                "verification_timestamp": datetime.now(timezone.utc).isoformat()
            }
        }

        # Store as MCard (content-addressable certificate)
        vcard_mcard = MCard(json.dumps(vcard_content, indent=2))
        vcard_hash = self.collection.add(vcard_mcard)

        self.logger.info(f"Generated VerificationVCard: {vcard_hash}")
        return vcard_hash
