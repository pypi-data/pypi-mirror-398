"""
Embedding Providers Package

Provides embedding generation capabilities for RAG.
"""

from .base import EmbeddingProvider
from .ollama import OllamaEmbeddingProvider
from .vision import VisionEmbeddingProvider, VISION_MODELS

__all__ = [
    'EmbeddingProvider',
    'OllamaEmbeddingProvider',
    'VisionEmbeddingProvider',
    'VISION_MODELS',
]

