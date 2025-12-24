"""
MLC LLM Provider Implementation

Provider for the MLC LLM REST API (OpenAI compatible).
Running via `mlc_llm serve`.
"""

import json
import logging
import urllib.request
import urllib.error
from typing import Any, Dict, List

from .base import LLMProvider
from ..config import LLM_PROVIDERS
from mcard.ptr.core.monads import Either, Left, Right


class MLCLLMProvider(LLMProvider):
    """
    MLC LLM provider for local execution via OpenAI-compatible API.
    
    Compatible with:
    - /v1/completions
    - /v1/chat/completions
    - /v1/models
    """
    
    provider_name = "mlc-llm"
    
    def __init__(self, base_url: str = None, timeout: int = 120):
        self.logger = logging.getLogger(__name__)
        self.config = LLM_PROVIDERS['mlc-llm']
        self.base_url = (base_url or self.config['base_url']).rstrip('/')
        self.timeout = timeout
    
    def _make_request(
        self, 
        endpoint: str, 
        data: Dict = None, 
        method: str = 'POST'
    ) -> Either[str, Dict]:
        """Make HTTP request to MLC LLM API."""
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
                return Right(json.loads(response_text))
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            return Left(f"MLC-LLM HTTP error {e.code}: {error_body}")
        except urllib.error.URLError as e:
            return Left(f"MLC-LLM connection error: {e.reason}")
        except json.JSONDecodeError as e:
            return Left(f"MLC-LLM response parse error: {e}")
        except Exception as e:
            return Left(f"MLC-LLM request failed: {e}")
    
    def complete(self, prompt: str, params: Dict[str, Any]) -> Either[str, str]:
        """
        Generate text completion.
        Using /v1/completions style.
        """
        data = {
            'model': params.get('model', self.config['default_model']),
            'prompt': prompt,
            'max_tokens': params.get('max_tokens', 128),
            'temperature': params.get('temperature', 0.7),
            'top_p': params.get('top_p', 1.0),
            'stream': False,
        }
        
        if 'stop' in params:
            data['stop'] = params['stop']
            
        self.logger.debug(f"MLC-LLM complete request: model={data['model']}")
        
        result = self._make_request(self.config['api_path'], data)
        
        if result.is_left():
            return result
        
        response = result.value
        # OpenAI format: {'choices': [{'text': '...'}]}
        if 'choices' in response and len(response['choices']) > 0:
            return Right(response['choices'][0].get('text', ''))
        elif 'error' in response:
            return Left(f"MLC-LLM error: {response['error']}")
        else:
            return Left(f"Unexpected MLC-LLM response format: {response}")
    
    def chat(
        self, 
        messages: List[Dict[str, str]], 
        params: Dict[str, Any]
    ) -> Either[str, Dict[str, Any]]:
        """
        Generate chat completion.
        Using /v1/chat/completions style.
        """
        data = {
            'model': params.get('model', self.config['default_model']),
            'messages': messages,
            'max_tokens': params.get('max_tokens', 128),
            'temperature': params.get('temperature', 0.7),
            'top_p': params.get('top_p', 1.0),
            'stream': False,
        }
        
        if 'stop' in params:
            data['stop'] = params['stop']
            
        self.logger.debug(f"MLC-LLM chat request: model={data['model']}")
        
        result = self._make_request(self.config['chat_path'], data)
        
        if result.is_left():
            return result
        
        response = result.value
        # OpenAI format: {'choices': [{'message': {'role': 'assistant', 'content': '...'}}]}
        if 'choices' in response and len(response['choices']) > 0:
            choice = response['choices'][0]
            message = choice.get('message', {})
            return Right({
                'content': message.get('content', ''),
                'role': message.get('role', 'assistant'),
                'model': response.get('model', data['model']),
                'usage': response.get('usage', {})
            })
        elif 'error' in response:
            return Left(f"MLC-LLM error: {response['error']}")
        else:
            return Left(f"Unexpected MLC-LLM response format: {response}")
    
    def validate_connection(self) -> bool:
        """Check if MLC-LLM service is running via models endpoint."""
        try:
            result = self._make_request(self.config['models_path'], method='GET')
            return result.is_right()
        except Exception:
            return False
    
    def list_models(self) -> Either[str, List[str]]:
        """List available api models."""
        result = self._make_request(self.config['models_path'], method='GET')
        
        if result.is_left():
            return result
        
        response = result.value
        # OpenAI format: {'data': [{'id': 'model-id', ...}]}
        if 'data' in response and isinstance(response['data'], list):
            models = [m.get('id', 'unknown') for m in response['data']]
            return Right(models)
        else:
            return Left(f"Unexpected models response: {response}")
