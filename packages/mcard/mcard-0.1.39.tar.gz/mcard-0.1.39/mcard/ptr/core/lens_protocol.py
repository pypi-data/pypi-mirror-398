"""
Lens Protocol - JSON-RPC 2.0 interface for PTR communication

Implements the transport-agnostic Lens Protocol that operationalizes
CLM verification and execution through standardized RPC methods.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional


from .common_types import ExecutionResult

# Forward declarations to avoid circular imports
class PTREngine:
    pass


@dataclass
class LensRequest:
    """JSON-RPC 2.0 request structure"""
    jsonrpc: str = "2.0"
    method: str = ""
    params: dict[str, Any] = None
    id: Optional[str] = None


@dataclass
class LensResponse:
    """JSON-RPC 2.0 response structure"""
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[dict[str, Any]] = None
    id: Optional[str] = None


class LensProtocol:
    """
    Implementation of the Lens Protocol for PTR communication.

    The Lens Protocol provides a standardized JSON-RPC 2.0 interface for:
    - PCard execution
    - CLM verification
    - Lens revelation (extracting aspects from cards)
    - Status and health checks
    """

    def __init__(self, engine):
        # Import here to avoid circular import
        from .engine import PTREngine

        if not isinstance(engine, PTREngine):
            raise TypeError("engine must be a PTREngine instance")

        self.engine = engine
        self.logger = logging.getLogger(__name__)
        self.method_handlers = {
            "pcard.execute": self.handle_pcard_execute,
            "pcard.verify": self.handle_pcard_verify,
            "lens.reveal": self.handle_lens_reveal,
            "system.status": self.handle_system_status,
            "system.health": self.handle_system_health,
        }

    def handle_request(self, request_json: str) -> str:
        """
        Handle a JSON-RPC 2.0 request and return response.

        Args:
            request_json: JSON-RPC 2.0 request as JSON string

        Returns:
            JSON-RPC 2.0 response as JSON string
        """
        try:
            # Parse request
            request_data = json.loads(request_json)
            request = LensRequest(**request_data)

            self.logger.info(f"Processing Lens request: {request.method}")

            # Validate JSON-RPC version
            if request.jsonrpc != "2.0":
                raise ValueError("Invalid JSON-RPC version")

            # Find method handler
            if request.method not in self.method_handlers:
                raise ValueError(f"Unknown method: {request.method}")

            # Execute method
            handler = self.method_handlers[request.method]
            result = handler(request.params or {})

            # Create success response
            response = LensResponse(
                result=result,
                id=request.id
            )

            self.logger.info(f"Lens request {request.method} completed successfully")

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in request: {str(e)}")
            response = LensResponse(
                error={
                    "code": -32700,
                    "message": "Parse error",
                    "data": str(e)
                },
                id=request.id if 'request' in locals() else None
            )

        except Exception as e:
            self.logger.error(f"Lens request error: {str(e)}")
            response = LensResponse(
                error={
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e)
                },
                id=request.id if 'request' in locals() else None
            )

        return json.dumps(response.__dict__, default=str)

    def handle_pcard_execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a PCard against a target after CLM verification.

        Required params:
        - pcard_hash: Hash of the PCard to execute
        - target_hash: Hash of the target MCard/VCard
        - context: Optional execution context
        """
        required_params = ['pcard_hash', 'target_hash']
        for param in required_params:
            if param not in params:
                raise ValueError(f"Missing required parameter: {param}")

        pcard_hash = params['pcard_hash']
        target_hash = params['target_hash']
        context = params.get('context', {})

        # Execute PCard
        result = self.engine.execute_pcard(pcard_hash, target_hash, context)

        return {
            "success": result.success,
            "output": result.output,
            "verification_vcard": result.verification_vcard,
            "execution_time_ms": result.execution_time_ms,
            "error_message": result.error_message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def handle_pcard_verify(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Verify CLM consistency without execution.

        Required params:
        - pcard_hash: Hash of the PCard to verify
        - target_hash: Hash of the target MCard/VCard
        - context: Optional verification context
        """
        required_params = ['pcard_hash', 'target_hash']
        for param in required_params:
            if param not in params:
                raise ValueError(f"Missing required parameter: {param}")

        pcard_hash = params['pcard_hash']
        target_hash = params['target_hash']
        context = params.get('context', {})

        # Load PCard and target
        pcard = self.engine.collection.get(pcard_hash)
        target = self.engine.collection.get(target_hash)

        if not pcard:
            raise ValueError(f"PCard not found: {pcard_hash}")
        if not target:
            raise ValueError(f"Target not found: {target_hash}")

        # Verify CLM consistency
        verification_result = self.engine.verifier.verify_clm_consistency(pcard, target, context)

        return {
            "is_valid": verification_result.is_valid,
            "abstract_valid": verification_result.abstract_valid,
            "concrete_valid": verification_result.concrete_valid,
            "balanced_valid": verification_result.balanced_valid,
            "errors": verification_result.errors,
            "warnings": verification_result.warnings,
            "verification_details": verification_result.verification_details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def handle_lens_reveal(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Extract a specific aspect from a card using the lens principle.

        Required params:
        - card_hash: Hash of the card to reveal
        - aspect: Aspect to reveal (e.g., 'permissions', 'metadata', 'clm_dimensions')
        """
        required_params = ['card_hash', 'aspect']
        for param in required_params:
            if param not in params:
                raise ValueError(f"Missing required parameter: {param}")

        card_hash = params['card_hash']
        aspect = params['aspect']

        # Load card
        card = self.engine.collection.get(card_hash)
        if not card:
            raise ValueError(f"Card not found: {card_hash}")

        # Reveal aspect based on type
        if aspect == 'permissions':
            revealed = self._reveal_permissions(card)
        elif aspect == 'metadata':
            revealed = self._reveal_metadata(card)
        elif aspect == 'clm_dimensions':
            revealed = self._reveal_clm_dimensions(card)
        elif aspect == 'content_type':
            revealed = self._reveal_content_type(card)
        else:
            revealed = {"error": f"Unknown aspect: {aspect}"}

        return {
            "card_hash": card_hash,
            "aspect": aspect,
            "revealed": revealed,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def handle_system_status(self, params: dict[str, Any]) -> dict[str, Any]:
        """Get system status and statistics."""
        collection_stats = {
            "total_cards": self.engine.collection.count(),
            "cached_executions": len(self.engine.execution_cache),
            "cached_verifications": len(self.engine.verifier.verification_cache)
        }

        return {
            "status": "operational",
            "version": "0.1.0",
            "engine": "PTR",
            "collection_stats": collection_stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def handle_system_health(self, params: dict[str, Any]) -> dict[str, Any]:
        """Perform health check."""
        health_checks = {
            "database": self._check_database_health(),
            "cache": self._check_cache_health(),
            "verification": self._check_verification_health()
        }

        overall_healthy = all(check["healthy"] for check in health_checks.values())

        return {
            "healthy": overall_healthy,
            "checks": health_checks,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _reveal_permissions(self, card) -> dict[str, Any]:
        """Reveal permissions aspect of a card."""
        try:
            content = card.get_content().decode('utf-8')
            import yaml
            card_data = yaml.safe_load(content)

            permissions = card_data.get('permissions', {
                "read": True,
                "execute": True,
                "modify": False
            })

            return permissions
        except Exception as e:
            return {"error": f"Failed to reveal permissions: {str(e)}"}

    def _reveal_metadata(self, card) -> dict[str, Any]:
        """Reveal metadata aspect of a card."""
        return {
            "hash": card.hash,
            "g_time": card.g_time.isoformat() if card.g_time else None,
            "content_type": card.get_content_type(),
            "content_size": len(card.get_content())
        }

    def _reveal_clm_dimensions(self, card) -> dict[str, Any]:
        """Reveal CLM dimensions of a card."""
        try:
            content = card.get_content().decode('utf-8')
            import yaml
            card_data = yaml.safe_load(content)

            return {
                "has_abstract": 'abstract' in card_data,
                "has_concrete": 'concrete' in card_data,
                "has_balanced": 'balanced' in card_data,
                "is_clm_compliant": all(dim in card_data for dim in ['abstract', 'concrete', 'balanced'])
            }
        except Exception as e:
            return {"error": f"Failed to reveal CLM dimensions: {str(e)}"}

    def _reveal_content_type(self, card) -> dict[str, Any]:
        """Reveal content type information."""
        return {
            "mime_type": card.get_content_type(),
            "is_text": card.get_content_type().startswith('text/'),
            "is_binary": not card.get_content_type().startswith('text/')
        }

    def _check_database_health(self) -> dict[str, Any]:
        """Check database connectivity."""
        try:
            count = self.engine.collection.count()
            return {"healthy": True, "details": f"Connected, {count} cards"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    def _check_cache_health(self) -> dict[str, Any]:
        """Check cache system."""
        try:
            cache_size = len(self.engine.execution_cache)
            return {"healthy": True, "details": f"Cache contains {cache_size} entries"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    def _check_verification_health(self) -> dict[str, Any]:
        """Check verification system."""
        try:
            cache_size = len(self.engine.verifier.verification_cache)
            return {"healthy": True, "details": f"Verification cache contains {cache_size} entries"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
