"""
Ollama Provider Implementation

Provider for the Ollama local LLM service.
https://ollama.ai/
"""

import json
import logging
import urllib.request
import urllib.error
from typing import Any, Dict, List

from .base import LLMProvider
from ..config import LLM_PROVIDERS
from mcard.ptr.core.monads import Either, Left, Right


class OllamaProvider(LLMProvider):
    """
    Ollama LLM provider for local model execution.
    
    Ollama provides a simple API for running LLMs locally:
    - /api/generate - Text completion
    - /api/chat - Chat completion
    - /api/tags - List available models
    """
    
    provider_name = "ollama"
    
    def __init__(self, base_url: str = None, timeout: int = 120):
        self.logger = logging.getLogger(__name__)
        self.config = LLM_PROVIDERS['ollama']
        self.base_url = (base_url or self.config['base_url']).rstrip('/')
        self.timeout = timeout
    
    def _make_request(
        self, 
        endpoint: str, 
        data: Dict = None, 
        method: str = 'POST'
    ) -> Either[str, Dict]:
        """Make HTTP request to Ollama API."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if data:
                request = urllib.request.Request(
                    url,
                    data=json.dumps(data).encode('utf-8'),
                    headers={'Content-Type': 'application/json'},
                    method=method
                )
            else:
                request = urllib.request.Request(url, method=method)
            
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                response_text = response.read().decode('utf-8')
                
                # Handle streaming response (multiple JSON objects)
                if '\n' in response_text and not response_text.strip().startswith('{'):
                    # Parse last complete response for final result
                    lines = [l for l in response_text.strip().split('\n') if l]
                    if lines:
                        return Right(json.loads(lines[-1]))
                
                return Right(json.loads(response_text))
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            return Left(f"Ollama HTTP error {e.code}: {error_body}")
        except urllib.error.URLError as e:
            return Left(f"Ollama connection error: {e.reason}")
        except json.JSONDecodeError as e:
            return Left(f"Ollama response parse error: {e}")
        except Exception as e:
            return Left(f"Ollama request failed: {e}")
    
    def complete(self, prompt: str, params: Dict[str, Any]) -> Either[str, str]:
        """
        Generate text completion using Ollama's /api/generate endpoint.
        
        Args:
            prompt: The input prompt
            params: Generation parameters (model, options, etc.)
            
        Returns:
            Either[Error, Completion]
        """
        data = {
            'model': params.get('model', self.config['default_model']),
            'prompt': prompt,
            'stream': False,  # Disable streaming for simpler handling
        }
        
        # Add options if present
        if 'options' in params:
            data['options'] = params['options']
        
        self.logger.debug(f"Ollama generate request: model={data['model']}")
        
        result = self._make_request(self.config['api_path'], data)
        
        if result.is_left():
            return result
        
        response = result.value
        if 'response' in response:
            return Right(response['response'])
        elif 'error' in response:
            return Left(f"Ollama error: {response['error']}")
        else:
            return Left(f"Unexpected Ollama response format: {response}")
    
    def chat(
        self, 
        messages: List[Dict[str, str]], 
        params: Dict[str, Any]
    ) -> Either[str, Dict[str, Any]]:
        """
        Generate chat completion using Ollama's /api/chat endpoint.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            params: Generation parameters
            
        Returns:
            Either[Error, ResponseDict]
        """
        data = {
            'model': params.get('model', self.config['default_model']),
            'messages': messages,
            'stream': False,
        }
        
        # Add options if present
        if 'options' in params:
            data['options'] = params['options']
        
        self.logger.debug(f"Ollama chat request: model={data['model']}, messages={len(messages)}")
        
        result = self._make_request(self.config['chat_path'], data)
        
        if result.is_left():
            return result
        
        response = result.value
        if 'message' in response:
            return Right({
                'content': response['message'].get('content', ''),
                'role': response['message'].get('role', 'assistant'),
                'model': response.get('model', data['model']),
                'done': response.get('done', True),
                'total_duration': response.get('total_duration'),
                'eval_count': response.get('eval_count'),
            })
        elif 'error' in response:
            return Left(f"Ollama error: {response['error']}")
        else:
            return Left(f"Unexpected Ollama chat response format: {response}")
    
    def validate_connection(self) -> bool:
        """Check if Ollama service is running."""
        try:
            result = self._make_request(self.config['models_path'], method='GET')
            return result.is_right()
        except Exception:
            return False
    
    def list_models(self) -> Either[str, List[str]]:
        """List available models in Ollama."""
        result = self._make_request(self.config['models_path'], method='GET')
        
        if result.is_left():
            return result
        
        response = result.value
        if 'models' in response:
            models = [m.get('name', m.get('model', 'unknown')) for m in response['models']]
            return Right(models)
        else:
            return Left(f"Unexpected models response: {response}")
    
    def pull_model(self, model_name: str) -> Either[str, str]:
        """Pull a model from Ollama library."""
        data = {'name': model_name, 'stream': False}
        result = self._make_request('/api/pull', data)
        
        if result.is_left():
            return result
        
        return Right(f"Model {model_name} pulled successfully")
