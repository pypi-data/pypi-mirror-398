"""
RAG Configuration Module

Centralized configuration for RAG components including embedding models,
vector search parameters, and storage settings.
"""

from dataclasses import dataclass, field
from typing import Optional, List

# ─────────────────────────────────────────────────────────────────────────────
# Embedding Model Configurations
# ─────────────────────────────────────────────────────────────────────────────

EMBEDDING_MODELS = {
    'nomic-embed-text': {
        'dimensions': 768,
        'provider': 'ollama',
        'max_tokens': 8192,
        'description': 'High quality, general purpose embeddings',
    },
    'bge-m3': {
        'dimensions': 1024,
        'provider': 'ollama',
        'max_tokens': 8192,
        'description': 'Multi-lingual, multi-granularity embeddings',
    },
    'mxbai-embed-large': {
        'dimensions': 1024,
        'provider': 'ollama',
        'max_tokens': 512,
        'description': 'High quality embeddings for retrieval',
    },
    'all-minilm': {
        'dimensions': 384,
        'provider': 'ollama',
        'max_tokens': 256,
        'description': 'Fast, lightweight embeddings',
    },
}

# Default embedding model
DEFAULT_EMBEDDING_MODEL = 'nomic-embed-text'

# ─────────────────────────────────────────────────────────────────────────────
# Vision Models for Multimodal Embedding
# ─────────────────────────────────────────────────────────────────────────────

VISION_MODELS = {
    'moondream': {
        'size': '1.7GB',
        'description': 'Moondream - Tiny, high-performance vision language model',
        'capabilities': ['image_description', 'visual_qa'],
    },
    'llama3.2-vision': {
        'size': '7.9GB',
        'description': 'Llama 3.2 Vision - 11B multimodal model with strong OCR',
        'capabilities': ['image_description', 'ocr', 'visual_qa'],
    },
    'llava': {
        'size': '4.7GB',
        'description': 'LLaVA - Large Language and Vision Assistant',
        'capabilities': ['image_description', 'visual_qa'],
    },
    'minicpm-v': {
        'size': '5.6GB',
        'description': 'MiniCPM-V - Efficient vision-language model',
        'capabilities': ['image_description', 'ocr', 'multi_image'],
    },
}

DEFAULT_VISION_MODEL = 'moondream'

# ─────────────────────────────────────────────────────────────────────────────
# Vector Search Configuration
# ─────────────────────────────────────────────────────────────────────────────

# Distance metrics supported by sqlite-vec
DISTANCE_METRICS = ('L2', 'cosine', 'L1')
DEFAULT_DISTANCE_METRIC = 'cosine'

# Default search parameters
DEFAULT_TOP_K = 5
MAX_TOP_K = 100

# Chunking configuration
DEFAULT_CHUNK_SIZE = 1000  # characters
DEFAULT_CHUNK_OVERLAP = 200

# ─────────────────────────────────────────────────────────────────────────────
# RAG Configuration Dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RAGConfig:
    """
    Configuration for MCard RAG system.
    
    Attributes:
        embedding_model: Name of the embedding model to use
        embedding_provider: Provider for embeddings (ollama, openai, etc.)
        ollama_base_url: Base URL for Ollama API
        vector_db_path: Path to vector database (None = use main MCard db)
        distance_metric: Distance metric for similarity search
        top_k: Default number of results to return
        chunk_size: Maximum characters per chunk
        chunk_overlap: Overlap between chunks
        enable_hybrid_search: Enable FTS + vector hybrid search
        rerank_results: Re-rank results using cross-encoder
    """
    
    # Embedding configuration
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    embedding_provider: str = 'ollama'
    ollama_base_url: str = 'http://localhost:11434'
    
    # Vector storage
    vector_db_path: Optional[str] = None  # None = same as MCard db
    distance_metric: str = DEFAULT_DISTANCE_METRIC
    
    # Search parameters
    top_k: int = DEFAULT_TOP_K
    similarity_threshold: float = 0.0  # Minimum similarity (0-1)
    
    # Chunking
    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    
    # Advanced features
    enable_hybrid_search: bool = True
    rerank_results: bool = False
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.embedding_model not in EMBEDDING_MODELS:
            raise ValueError(f"Unknown embedding model: {self.embedding_model}. "
                           f"Available: {list(EMBEDDING_MODELS.keys())}")
        
        if self.distance_metric not in DISTANCE_METRICS:
            raise ValueError(f"Unknown distance metric: {self.distance_metric}. "
                           f"Available: {DISTANCE_METRICS}")
        
        if self.top_k < 1 or self.top_k > MAX_TOP_K:
            raise ValueError(f"top_k must be between 1 and {MAX_TOP_K}")
    
    @property
    def dimensions(self) -> int:
        """Get embedding dimensions for the configured model."""
        return EMBEDDING_MODELS[self.embedding_model]['dimensions']
    
    @property
    def max_tokens(self) -> int:
        """Get max tokens for the configured model."""
        return EMBEDDING_MODELS[self.embedding_model]['max_tokens']


# Default configuration
DEFAULT_RAG_CONFIG = RAGConfig()
