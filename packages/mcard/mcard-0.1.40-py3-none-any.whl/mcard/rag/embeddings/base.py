"""
Embedding Provider Base Class

Abstract interface for embedding providers.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class EmbeddingResult:
    """Result from an embedding operation."""
    vector: List[float]
    model: str
    dimensions: int
    token_count: Optional[int] = None


class EmbeddingProvider(ABC):
    """
    Abstract base class for embedding providers.
    
    Implementations should handle:
    - Connection to the embedding service
    - Text preprocessing (truncation, etc.)
    - Batch processing for efficiency
    - Error handling and retries
    """
    
    provider_name: str = "base"
    model_name: str
    dimensions: int
    
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """
        Generate embedding vector for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        pass
    
    @abstractmethod
    def validate_connection(self) -> bool:
        """
        Check if the embedding service is available.
        
        Returns:
            True if connection is valid
        """
        pass
    
    def get_info(self) -> dict:
        """Get provider information."""
        return {
            'provider': self.provider_name,
            'model': self.model_name,
            'dimensions': self.dimensions,
            'available': self.validate_connection(),
        }
