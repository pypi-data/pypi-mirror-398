from typing import Any, Dict, Optional, Union
import base64
from mcard import MCard
from mcard.model.card import MCardFromData

class MCardSerialization:
    """Helper for serializing/deserializing MCards for network transmission."""

    @staticmethod
    def serialize(card: MCard) -> Dict[str, Any]:
        """Serialize an MCard to a JSON-safe payload."""
        content = card.get_content()
        if isinstance(content, str):
            content = content.encode("utf-8")
        
        # Handle hash_function which might be an enum
        hash_func = getattr(card, "hash_function", "sha256")
        if hasattr(hash_func, "value"):
            hash_func = hash_func.value
        elif hasattr(hash_func, "name"):
            hash_func = hash_func.name
        else:
            hash_func = str(hash_func)
        
        return {
            "hash": card.hash,
            "content": base64.b64encode(content).decode("ascii"),
            "g_time": card.g_time,
            "content_type": getattr(card, "content_type", "application/octet-stream"),
            "hash_function": hash_func,
        }

    @staticmethod
    def deserialize(payload: Dict[str, Any]) -> MCard:
        """Deserialize a JSON payload back to an MCard."""
        content_b64 = payload.get("content")
        if not content_b64:
            raise ValueError("Missing content in MCard payload")
        
        content = base64.b64decode(content_b64)
        
        if payload.get("hash") and payload.get("g_time"):
            # Reconstruct with existing identity using MCardFromData
            return MCardFromData(content, payload["hash"], payload["g_time"])
        
        # Create new identity
        return MCard(content)
