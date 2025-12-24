"""
Vision Embedding Provider

Multimodal embedding provider that uses vision models to describe images,
then embeds the descriptions for vector search.

This approach is recommended for image RAG since Ollama's embed API 
doesn't directly support image inputs.
"""

import base64
import json
import logging
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .base import EmbeddingProvider, EmbeddingResult
from .ollama import OllamaEmbeddingProvider

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Vision Models Configuration
# ─────────────────────────────────────────────────────────────────────────────

VISION_MODELS = {
    'moondream': {
        'description': 'Moondream - Tiny, high-performance vision language model',
        'size': '1.7GB',
    },
    'llama3.2-vision': {
        'description': 'Llama 3.2 Vision - 11B multimodal model',
        'size': '7.9GB',
    },
    'llava': {
        'description': 'LLaVA - Large Language and Vision Assistant',
        'size': '4.7GB',
    },
    'minicpm-v': {
        'description': 'MiniCPM-V - Efficient vision-language model',
        'size': '5.6GB',
    },
}

DEFAULT_VISION_MODEL = 'moondream'


# ─────────────────────────────────────────────────────────────────────────────
# Vision Embedding Provider
# ─────────────────────────────────────────────────────────────────────────────

class VisionEmbeddingProvider(EmbeddingProvider):
    """
    Multimodal embedding provider for images.
    
    Uses a two-stage approach:
    1. Vision model generates a text description of the image
    2. Text embedding model converts description to vector
    
    This enables semantic search over images using existing vector infrastructure.
    
    Usage:
        from mcard.rag.embeddings import VisionEmbeddingProvider
        
        provider = VisionEmbeddingProvider()
        
        # Embed an image
        embedding = provider.embed_image("/path/to/image.jpg")
        
        # Or with bytes
        with open("image.png", "rb") as f:
            embedding = provider.embed_image_bytes(f.read())
    """
    
    def __init__(
        self,
        vision_model: str = DEFAULT_VISION_MODEL,
        embedding_model: str = 'nomic-embed-text',
        base_url: str = 'http://localhost:11434',
        description_prompt: str = None
    ):
        """
        Initialize vision embedding provider.
        
        Args:
            vision_model: Ollama vision model for describing images
            embedding_model: Text embedding model
            base_url: Ollama API base URL
            description_prompt: Custom prompt for image description
        """
        self.vision_model = vision_model
        self.base_url = base_url.rstrip('/')
        
        # Text embedder for converting descriptions to vectors
        self.text_embedder = OllamaEmbeddingProvider(
            model=embedding_model,
            base_url=base_url
        )
        
        # Prompt for image description
        self.description_prompt = description_prompt or """Describe this image in detail for semantic search. 
Include:
- Main subject and objects visible
- Colors, textures, and visual elements
- Any text visible in the image
- Context, setting, or environment
- Actions or relationships between elements

Be comprehensive but concise. Focus on searchable details."""
    
    @property
    def model_name(self) -> str:
        """Return combined model identifier."""
        return f"vision:{self.vision_model}+{self.text_embedder.model_name}"
    
    @property
    def dimensions(self) -> int:
        """Return embedding dimensions (from text embedder)."""
        return self.text_embedder.dimensions
    
    @property
    def provider_name(self) -> str:
        return 'ollama-vision'
    
    def describe_image(
        self, 
        image_data: Union[str, bytes, Path],
        prompt: str = None
    ) -> str:
        """
        Generate text description of an image.
        
        Args:
            image_data: Image as file path, bytes, or base64 string
            prompt: Optional custom prompt
            
        Returns:
            Text description of the image
        """
        # Convert image to base64
        if isinstance(image_data, (str, Path)):
            path = Path(image_data)
            if path.exists():
                with open(path, 'rb') as f:
                    image_bytes = f.read()
                image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            else:
                # Assume it's already base64
                image_b64 = str(image_data)
        elif isinstance(image_data, bytes):
            image_b64 = base64.b64encode(image_data).decode('utf-8')
        else:
            raise ValueError(f"Unsupported image data type: {type(image_data)}")
        
        # Call vision model
        url = f"{self.base_url}/api/generate"
        
        payload = {
            'model': self.vision_model,
            'prompt': prompt or self.description_prompt,
            'images': [image_b64],
            'stream': False,
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('response', '')
        except Exception as e:
            logger.error(f"Vision model call failed: {e}")
            raise RuntimeError(f"Failed to describe image: {e}")
    
    def embed_image(
        self, 
        image_data: Union[str, bytes, Path],
        prompt: str = None
    ) -> List[float]:
        """
        Generate embedding for an image.
        
        Args:
            image_data: Image as file path, bytes, or base64 string
            prompt: Optional custom prompt for description
            
        Returns:
            Embedding vector
        """
        # Get description
        description = self.describe_image(image_data, prompt)
        
        if not description:
            raise ValueError("Vision model returned empty description")
        
        logger.debug(f"Image description: {description[:100]}...")
        
        # Embed description
        return self.text_embedder.embed(description)
    
    def embed_image_with_description(
        self, 
        image_data: Union[str, bytes, Path],
        prompt: str = None
    ) -> Tuple[List[float], str]:
        """
        Generate embedding and return description.
        
        Args:
            image_data: Image as file path, bytes, or base64
            prompt: Optional custom prompt
            
        Returns:
            Tuple of (embedding, description)
        """
        description = self.describe_image(image_data, prompt)
        embedding = self.text_embedder.embed(description)
        return embedding, description
    
    # Required EmbeddingProvider methods
    
    def embed(self, text: str) -> List[float]:
        """Embed text (delegates to text embedder)."""
        return self.text_embedder.embed(text)
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts."""
        return self.text_embedder.embed_batch(texts)
    
    def embed_images(
        self, 
        images: List[Union[str, bytes, Path]]
    ) -> List[List[float]]:
        """
        Embed multiple images.
        
        Args:
            images: List of image paths, bytes, or base64 strings
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        for img in images:
            try:
                embeddings.append(self.embed_image(img))
            except Exception as e:
                logger.error(f"Failed to embed image: {e}")
                # Return zero vector on failure
                embeddings.append([0.0] * self.dimensions)
        return embeddings
    
    def validate_connection(self) -> bool:
        """Validate both vision and embedding models are available."""
        # Check text embedder
        if not self.text_embedder.validate_connection():
            return False
        
        # Check vision model
        try:
            url = f"{self.base_url}/api/show"
            payload = json.dumps({'name': self.vision_model}).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=payload,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status == 200
        except Exception as e:
            logger.warning(f"Vision model check failed: {e}")
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """Get provider information."""
        return {
            'provider': self.provider_name,
            'vision_model': self.vision_model,
            'embedding_model': self.text_embedder.model_name,
            'dimensions': self.dimensions,
            'vision_models_available': list(VISION_MODELS.keys()),
        }
