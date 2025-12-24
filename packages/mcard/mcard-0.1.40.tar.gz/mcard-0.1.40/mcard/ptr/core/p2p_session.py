"""
P2P Chat Session for incremental session recording.

Manages the incremental recording of a P2P session into MCards.
Acts as a linked-list generator, where each MCard points to the previous one.

Matches the TypeScript P2PChatSession implementation.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from mcard import MCard
from mcard.model.card_collection import CardCollection


logger = logging.getLogger(__name__)


@dataclass
class SessionMessage:
    """A single message in a P2P session."""
    sender: str
    content: str
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))


@dataclass
class SessionSegmentPayload:
    """Payload structure for a session segment MCard."""
    type: str = "p2p_session_segment"
    session_id: str = ""
    sequence: int = 0
    messages: List[Dict[str, Any]] = field(default_factory=list)
    previous_hash: Optional[str] = None
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))


@dataclass
class SessionSummaryPayload:
    """Payload structure for a session summary MCard."""
    type: str = "p2p_session_summary"
    session_id: str = ""
    original_head_hash: Optional[str] = None
    full_transcript: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))


class P2PChatSession:
    """
    Manages the incremental recording of a P2P session into MCards.
    Acts as a linked-list generator, where each MCard points to the previous one.
    """
    
    def __init__(
        self,
        collection: CardCollection,
        session_id: str,
        max_buffer_size: int = 5,
        initial_head_hash: Optional[str] = None
    ):
        """
        Initialize a P2P chat session.
        
        Args:
            collection: The CardCollection to store session MCards
            session_id: Unique identifier for this session
            max_buffer_size: Number of messages before auto-checkpoint (default: 5)
            initial_head_hash: Hash of previous session head for resumption
        """
        self.collection = collection
        self.session_id = session_id
        self.max_buffer_size = max_buffer_size
        self.previous_hash = initial_head_hash
        self.buffer: List[SessionMessage] = []
        self.sequence = 0
    
    def add_message(self, sender: str, content: str) -> Optional[str]:
        """
        Add a message to the current session buffer.
        Automatically checkpoints if buffer exceeds size.
        
        Args:
            sender: The sender identifier
            content: The message content
            
        Returns:
            Checkpoint hash if buffer was flushed, None otherwise
        """
        self.buffer.append(SessionMessage(
            sender=sender,
            content=content,
            timestamp=int(time.time() * 1000)
        ))
        
        if len(self.buffer) >= self.max_buffer_size:
            return self.checkpoint()
        
        return None
    
    def checkpoint(self) -> str:
        """
        Force write the current buffer to a new MCard.
        
        Returns:
            The hash of the created checkpoint MCard
        """
        if not self.buffer:
            return self.previous_hash or ""
        
        # Build payload
        payload = SessionSegmentPayload(
            type="p2p_session_segment",
            session_id=self.session_id,
            sequence=self.sequence,
            messages=[
                {
                    "sender": msg.sender,
                    "content": msg.content,
                    "timestamp": msg.timestamp
                }
                for msg in self.buffer
            ],
            previous_hash=self.previous_hash,
            timestamp=int(time.time() * 1000)
        )
        
        # Create MCard
        card = MCard(json.dumps({
            "type": payload.type,
            "sessionId": payload.session_id,
            "sequence": payload.sequence,
            "messages": payload.messages,
            "previousHash": payload.previous_hash,
            "timestamp": payload.timestamp
        }))
        
        # Save to collection
        self.collection.add(card)
        
        # Update state
        self.previous_hash = card.hash
        self.sequence += 1
        self.buffer = []
        
        logger.info(f"[P2PSession] Checkpoint created: {card.hash} (Seq: {payload.sequence})")
        return card.hash
    
    def get_head_hash(self) -> Optional[str]:
        """
        Get the hash of the latest segment (Head of the list).
        
        Returns:
            The hash of the current head, or None if no checkpoints yet
        """
        return self.previous_hash
    
    def summarize(self, keep_originals: bool = False) -> str:
        """
        Compile all segments into one MCard and optionally remove original segments.
        
        Args:
            keep_originals: If True, preserve original segment MCards (default: False)
            
        Returns:
            The hash of the summary MCard
        """
        # 1. Flush any remaining buffer
        if self.buffer:
            self.checkpoint()
        
        head_to_use = self.previous_hash
        
        logger.info(f"[P2PSession] Summarizing session starting from head: {head_to_use}")
        
        # 2. Traverse and Collect
        if head_to_use:
            messages, hashes = self._traverse_chain(head_to_use)
        else:
            messages, hashes = [], []
        
        # 3. Create Summary MCard
        summary_payload = {
            "type": "p2p_session_summary",
            "sessionId": self.session_id,
            "originalHeadHash": head_to_use,
            "fullTranscript": messages,
            "timestamp": int(time.time() * 1000)
        }
        
        summary_card = MCard(json.dumps(summary_payload, indent=2))
        self.collection.add(summary_card)
        
        logger.info(f"[P2PSession] Summary created: {summary_card.hash}")
        
        # 4. Cleanup (Delete old segments)
        if not keep_originals:
            logger.info(f"[P2PSession] Cleaning up {len(hashes)} segment MCards...")
            for hash_val in hashes:
                try:
                    self.collection.delete(hash_val)
                except Exception as e:
                    logger.error(f"[P2PSession] Failed to delete segment {hash_val}: {e}")
            logger.info("[P2PSession] Cleanup complete.")
        else:
            logger.info(f"[P2PSession] Skipping cleanup (keepOriginals=True). Preserved {len(hashes)} segments.")
        
        return summary_card.hash
    
    def _traverse_chain(self, head_hash: str) -> Tuple[List[Dict], List[str]]:
        """
        Traverse the session chain from head to tail.
        
        Args:
            head_hash: The hash to start traversal from
            
        Returns:
            Tuple of (messages list, hashes list)
        """
        messages: List[Dict] = []
        hashes: List[str] = []
        current_hash: Optional[str] = head_hash
        
        while current_hash:
            hashes.append(current_hash)
            card = self.collection.get(current_hash)
            
            if not card:
                logger.warning(f"[P2PSession] Broken chain at {current_hash}")
                break
            
            try:
                content = card.get_content()
                if isinstance(content, bytes):
                    content = content.decode("utf-8")
                
                payload = json.loads(content)
                
                if payload.get("type") == "p2p_session_segment":
                    # Prepend messages since we're traversing backwards
                    segment_messages = payload.get("messages", [])
                    messages = segment_messages + messages
                    current_hash = payload.get("previousHash")
                else:
                    logger.warning(f"[P2PSession] Invalid card type at {current_hash}")
                    break
            except Exception as e:
                logger.error(f"[P2PSession] Parse error at {current_hash}: {e}")
                break
        
        return messages, hashes
