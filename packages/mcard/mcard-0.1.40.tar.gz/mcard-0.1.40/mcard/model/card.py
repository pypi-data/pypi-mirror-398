from typing import Union
import logging
from mcard.model.hash.validator import HashValidator, HashAlgorithm
from mcard.model.g_time import GTime


class MCard:
    """MCard - Content-addressable data container (Data Plane).
    
    DOTS Vocabulary Role: CARRIER
    =============================
    
    MCard is the **Carrier** in the Double Operadic Theory of Systems (DOTS).
    - Each MCard is an **Object** in the Carrier category Car(S)
    - Hash-links between MCards are **Morphisms** in Car(S)
    - The Carrier is the category of all actual data/systems
    
    EOS Role: Invariant Content (Galois Root)
    =========================================
    
    MCard provides the **Invariant Substrate** in Experimental-Operational Symmetry:
    - `Hash(Content)` is a **pure function** with no side effects
    - Same content in Dev = Same hash in Prod (environment-invariant)
    - This is the "Joint Reality" P(H,E) = P(E,H) in Bayesian terms
    
    MVP Cards Architecture: Data Plane
    ===================================
    
    ::
    
        ┌───────────────────────────────────────────────────────┐
        │               APPLICATION PLANE (VCard)               │
        │     Value Exchange / AuthN/AuthZ / Sovereign Memory   │
        └─────────────────────────┬─────────────────────────────┘
                                  │ (Policy Triggers)
        ┌─────────────────────────▼─────────────────────────────┐
        │                CONTROL PLANE (PCard)                  │
        │   Polynomial Functor Composition / Monadic Execution  │
        └─────────────────────────┬─────────────────────────────┘
                                  │ (Hash References)
        ┌─────────────────────────▼─────────────────────────────┐
        │                 DATA PLANE (MCard) ◀── YOU ARE HERE   │
        │   Immutable, Content-Addressable Storage / Monad      │
        └───────────────────────────────────────────────────────┘
    
    The Empty Schema Principle
    ==========================
    
    MCard embodies the Empty Schema Principle from the Wordless Book:
    - Schema contains NO domain-specific terms (only hash, content, g_time)
    - Domain customization happens via data (INSERT), not schema changes
    - Universal applicability: same structure for ANY domain
    
    Functional Requirements (from design docs)
    ==========================================
    
    +--------+--------------------------------+----------------------------------+
    | ID     | Requirement                    | Implementation                   |
    +--------+--------------------------------+----------------------------------+
    | M-1    | Content-addressable via hash   | self.hash = SHA-256(content)     |
    | M-2    | CRD-only (no UPDATE)           | Immutable, no __setattr__        |
    | M-3    | Include g_time for ordering    | self.g_time field                |
    | M-4    | Human-readable content         | get_content(as_text=True)        |
    | EOS-M1 | Hash is pure function          | No side effects in hash compute  |
    | EOS-M2 | Content is immutable           | Content set once in __init__     |
    +--------+--------------------------------+----------------------------------+
    
    Attributes:
        content (bytes): Raw bytes of the content (Carrier Object data)
        hash (str): SHA-256 cryptographic hash (Carrier Object identity)
        g_time (str): Global timestamp with algorithm identifier
        hash_function (HashAlgorithm): The hash algorithm used
    
    See Also:
        - docs/WorkingNotes/Permanent/Projects/PKC Kernel/MCard.md
        - docs/WorkingNotes/Hub/Theory/Integration/DOTS Vocabulary as Efficient Representation for ABC Curriculum.md
    """

    def __init__(self, content: Union[str, bytes], hash_function: Union[str, HashAlgorithm] = HashAlgorithm.get_default()):
        """Initialize an MCard with content.
        
        Args:
            content: The content to store. Can be string or bytes.
            
        Raises:
            ValueError: If content is None or empty
        """
        if content is None:
            raise ValueError("Content cannot be None")

        if hash_function is None:
            raise ValueError("hash_function cannot be None")    

        if isinstance(content, (str, bytes)) and len(content) == 0:
            raise ValueError("Content cannot be empty")

        self.content = content if isinstance(content, bytes) else content.encode('utf-8')

        self.hash_function = HashAlgorithm(hash_function)

        # Compute and log the hash
        self.hash = HashValidator.compute_hash(content, self.hash_function)
        logging.debug(f"Computed hash for content: {self.hash}")

        self.g_time = GTime.stamp_now(self.hash_function)

        # Cache the content type
        from mcard.model.interpreter import ContentTypeInterpreter
        interpreter = ContentTypeInterpreter()
        self._content_type, _ = interpreter.detect_content_type(self.content)

    def get_content(self, as_text: bool = False) -> Union[bytes, str]:
        """Get the content.
        
        Args:
            as_text: If True, returns the content as a string (decoded from UTF-8).
                    If False (default), returns raw bytes.
                    
        Returns:
            The content as either bytes (default) or string, depending on the as_text parameter.
            
        Note:
            The default behavior returns bytes for backward compatibility with existing code.
            To get content as text, explicitly use get_content(as_text=True).
        """
        if as_text and isinstance(self.content, bytes):
            try:
                return self.content.decode('utf-8')
            except UnicodeDecodeError:
                # If content is not valid UTF-8, return as bytes
                return self.content
        return self.content

    def get_hash(self) -> str:
        """Compute and return the hash of the content."""
        return self.hash

    def get_g_time(self) -> str:
        """Get the current GTime string computed from the current time."""
        return self.g_time

    def get_content_type(self):
        """Get the content type of the MCard content."""
        return self._content_type

    def to_dict(self):
        """Convert the MCard to a dictionary.
        
        Returns:
            dict: A dictionary representation of the MCard with content as string.
        """
        content = self.get_content()
        if isinstance(content, bytes):
            try:
                content = content.decode('utf-8')
            except UnicodeDecodeError:
                # If content is not valid UTF-8, keep as bytes
                pass

        return {
            'content': content,
            'hash': self.get_hash(),
            'g_time': self.get_g_time(),
            'content_type': self.get_content_type()
        }

    def to_display_dict(self) -> dict[str, str]:
        """Convert the MCard to a display-friendly dictionary.

        Returns:
            dict: A dictionary with formatted fields for display:
                - hash: The card's unique hash
                - content_type: The type of content in the card
                - created_at: Formatted creation timestamp
                - content_preview: A preview of the card's content (first 50 chars)
                - card_class: The class name of the card (for debugging)
        """
        try:
            # Get content safely
            content = self.get_content()
            content_str = str(content) if content is not None else ""
            
            # Create preview
            content_preview = content_str[:50] + ("..." if len(content_str) > 50 else "")

            # Format timestamp
            created_at = self.get_g_time()
            created_at_str = str(created_at)[:19] if created_at else "N/A"

            return {
                "hash": self.get_hash(),
                "content_type": self.get_content_type() or "unknown",
                "created_at": created_at_str,
                "content_preview": content_preview,
                "card_class": self.__class__.__name__,
            }
        except Exception as e:
            logging.error(f"Error processing card for display: {e}")
            return {}

    def get_dots_metadata(self, tight_refs: list[str] = None, loose_refs: list[str] = None):
        """Get DOTS vocabulary metadata for this MCard.
        
        Returns the DOTS role information that positions this MCard
        in the Double Operadic Theory of Systems framework.
        
        MCard is always a CARRIER object in the Data Plane.
        
        Args:
            tight_refs: Optional list of prerequisite MCard hashes (vertical composition)
            loose_refs: Optional list of alternative MCard hashes (horizontal composition)
            
        Returns:
            DOTSMetadata describing this card's role.
        """
        from mcard.model.dots import create_mcard_dots_metadata
        return create_mcard_dots_metadata(tight_refs, loose_refs)

class MCardFromData(MCard):
    """An MCard subclass that initializes from existing hash and g_time."""

    def __init__(self, content: bytes, hash_value: str, g_time_str: str):
        """Initialize an MCard from pre-existing hash and g_time.

        Args:
            content: The content (must be bytes).
            hash_value: The pre-computed hash value.
            g_time_str: The pre-existing g_time string.
            hash_function: The hash function used.
        
        Raises:
            TypeError: if content is not bytes
            ValudeError: If hash_value or g_time_str are None or empty.
        """
        if not isinstance(content, bytes):
            raise TypeError("Content must be bytes when initializing from existing data.")

        if not hash_value:
            raise ValueError("Hash value cannot be None or empty")

        if not g_time_str:
            raise ValueError("g_time string cannot be None or empty")

        self.content = content
        self.hash = hash_value
        self.g_time = g_time_str  # Directly assign the provided g_time string
        self.hash_function = GTime.get_hash_function(self.g_time)

        # Cache the content type
        from mcard.model.interpreter import ContentTypeInterpreter
        interpreter = ContentTypeInterpreter()
        self._content_type, _ = interpreter.detect_content_type(self.content)

        logging.debug(f"Initialized MCard from existing data: {self.hash}")
