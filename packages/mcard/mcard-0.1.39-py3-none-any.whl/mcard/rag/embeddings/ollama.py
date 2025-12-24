"""
Ollama Embedding Provider

Generates embeddings using Ollama's local embedding models.
"""

import json
import logging
import urllib.request
import urllib.error
from typing import List, Optional

from .base import EmbeddingProvider
from ..config import EMBEDDING_MODELS, DEFAULT_EMBEDDING_MODEL

logger = logging.getLogger(__name__)


class OllamaEmbeddingProvider(EmbeddingProvider):
    """
    Embedding provider using Ollama's embedding API.
    
    Supports models like:
    - nomic-embed-text (768 dimensions)
    - bge-m3 (1024 dimensions)
    - mxbai-embed-large (1024 dimensions)
    - all-minilm (384 dimensions)
    
    Usage:
        provider = OllamaEmbeddingProvider('nomic-embed-text')
        vector = provider.embed("Hello world")
    """
    
    provider_name = "ollama"
    
    def __init__(
        self, 
        model: str = DEFAULT_EMBEDDING_MODEL,
        base_url: str = 'http://localhost:11434',
        timeout: int = 60
    ):
        """
        Initialize Ollama embedding provider.
        
        Args:
            model: Ollama embedding model name
            base_url: Ollama API base URL
            timeout: Request timeout in seconds
        """
        self.model_name = model
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        
        # Get dimensions from config or default
        if model in EMBEDDING_MODELS:
            self.dimensions = EMBEDDING_MODELS[model]['dimensions']
        else:
            # Unknown model, will determine dimensions on first embed
            self.dimensions = 0
            logger.warning(f"Unknown model '{model}', dimensions will be determined on first embed")
    
    def _make_request(self, endpoint: str, data: dict) -> dict:
        """Make HTTP request to Ollama API."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            request = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode('utf-8'))
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            raise RuntimeError(f"Ollama HTTP error {e.code}: {error_body}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Ollama connection error: {e.reason}")
        except Exception as e:
            raise RuntimeError(f"Ollama request failed: {e}")
    
    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")
        
        response = self._make_request('/api/embed', {
            'model': self.model_name,
            'input': text,
        })
        
        if 'embeddings' in response and response['embeddings']:
            embedding = response['embeddings'][0]
            
            # Update dimensions if unknown
            if self.dimensions == 0:
                self.dimensions = len(embedding)
                logger.info(f"Determined {self.model_name} dimensions: {self.dimensions}")
            
            return embedding
        else:
            raise RuntimeError(f"Unexpected Ollama response: {response}")
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Ollama supports batch embedding with the 'input' parameter as a list.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Filter empty texts
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            raise ValueError("All texts are empty")
        
        response = self._make_request('/api/embed', {
            'model': self.model_name,
            'input': valid_texts,
        })
        
        if 'embeddings' in response:
            embeddings = response['embeddings']
            
            # Update dimensions if unknown
            if self.dimensions == 0 and embeddings:
                self.dimensions = len(embeddings[0])
            
            return embeddings
        else:
            raise RuntimeError(f"Unexpected Ollama batch response: {response}")
    
    def validate_connection(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            # Check if server is running
            request = urllib.request.Request(
                f"{self.base_url}/api/tags",
                method='GET'
            )
            
            with urllib.request.urlopen(request, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                # Check if model is available
                if 'models' in data:
                    available_models = [m.get('name', '') for m in data['models']]
                    
                    # Check exact match or partial match
                    for model in available_models:
                        if self.model_name in model or model in self.model_name:
                            return True
                    
                    logger.warning(f"Model '{self.model_name}' not found. "
                                 f"Available: {available_models[:5]}...")
                    return False
                
                return True
                
        except Exception as e:
            logger.debug(f"Ollama validation failed: {e}")
            return False
    
    def pull_model(self) -> bool:
        """Pull the embedding model from Ollama."""
        try:
            response = self._make_request('/api/pull', {
                'name': self.model_name,
                'stream': False,
            })
            return True
        except Exception as e:
            logger.error(f"Failed to pull model {self.model_name}: {e}")
            return False
