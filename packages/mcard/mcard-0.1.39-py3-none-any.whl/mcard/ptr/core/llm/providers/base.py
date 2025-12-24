"""
LLM Provider Base Class

Abstract base class defining the interface for LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from mcard.ptr.core.monads import Either, Left, Right


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    Implementations should handle:
    - Connection to the LLM service
    - Request formatting for the specific API
    - Response parsing
    - Error handling
    """
    
    provider_name: str = "base"
    
    @abstractmethod
    def complete(self, prompt: str, params: Dict[str, Any]) -> Either[str, str]:
        """
        Generate text completion for a prompt.
        
        Args:
            prompt: The input prompt
            params: Provider-specific generation parameters
            
        Returns:
            Either[Error, Response]: Left(error) or Right(completion)
        """
        pass
    
    @abstractmethod
    def chat(
        self, 
        messages: List[Dict[str, str]], 
        params: Dict[str, Any]
    ) -> Either[str, Dict[str, Any]]:
        """
        Generate chat completion from messages.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            params: Provider-specific generation parameters
            
        Returns:
            Either[Error, Response]: Left(error) or Right(response dict)
        """
        pass
    
    @abstractmethod
    def validate_connection(self) -> bool:
        """
        Check if the provider service is available.
        
        Returns:
            True if connection is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def list_models(self) -> Either[str, List[str]]:
        """
        List available models from the provider.
        
        Returns:
            Either[Error, ModelList]: Left(error) or Right(list of model names)
        """
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get provider status information.
        
        Returns:
            Dictionary with provider status details
        """
        available = self.validate_connection()
        models_result = self.list_models() if available else Left("Not connected")
        
        return {
            'provider': self.provider_name,
            'available': available,
            'models': models_result.value if models_result.is_right() else [],
            'error': models_result.value if models_result.is_left() else None,
        }
