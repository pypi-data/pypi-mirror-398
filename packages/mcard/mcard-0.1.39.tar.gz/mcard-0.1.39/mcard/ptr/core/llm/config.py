"""
LLM Configuration Module

Centralized configuration for LLM providers and execution parameters.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

# ─────────────────────────────────────────────────────────────────────────────
# Provider Configurations
# ─────────────────────────────────────────────────────────────────────────────

LLM_PROVIDERS = {
    'ollama': {
        'base_url': 'http://localhost:11434',
        'api_path': '/api/generate',
        'chat_path': '/api/chat',
        'models_path': '/api/tags',
        'default_model': 'gemma3:latest',
        'available_models': ['gemma3:latest', 'llama3:latest', 'qwen3:latest'],
    },
    'mlc-llm': {
        'base_url': 'http://localhost:8000',
        'api_path': '/v1/completions',
        'chat_path': '/v1/chat/completions',
        'models_path': '/v1/models',
        'default_model': 'Llama-3-8B-Instruct-q4f16_1-MLC',
        'available_models': [],
    },
    'lmstudio': {
        'base_url': 'http://localhost:1234',
        'api_path': '/v1/completions',
        'chat_path': '/v1/chat/completions',
        'models_path': '/v1/models',
        'default_model': 'local-model',
        'available_models': [],
    },
    'openai': {
        'base_url': 'https://api.openai.com',
        'api_path': '/v1/completions',
        'chat_path': '/v1/chat/completions',
        'models_path': '/v1/models',
        'default_model': 'gpt-4',
        'available_models': ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'],
    },
    'anthropic': {
        'base_url': 'https://api.anthropic.com',
        'api_path': '/v1/messages',
        'chat_path': '/v1/messages',
        'models_path': None,
        'default_model': 'claude-3-sonnet-20240229',
        'available_models': ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Default Configuration
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_LLM_CONFIG = {
    'temperature': 0.7,
    'max_tokens': 2048,
    'top_p': 1.0,
    'top_k': 40,
    'timeout': 120,
    'stream': False,
    'response_format': 'text',
    'retry_count': 3,
    'retry_delay': 1.0,
}

# Output format options
RESPONSE_FORMATS = ('text', 'json', 'structured', 'markdown')

# Default provider
DEFAULT_PROVIDER = 'ollama'


# ─────────────────────────────────────────────────────────────────────────────
# LLMConfig Dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class LLMConfig:
    """
    Configuration for LLM execution.
    
    Supports multiple providers (Ollama, LMStudio, OpenAI, Anthropic) with
    unified configuration interface.
    """
    
    # Provider settings
    provider: str = DEFAULT_PROVIDER
    model: Optional[str] = None  # Uses provider default if None
    endpoint_url: Optional[str] = None  # Override provider base_url
    api_key: Optional[str] = None  # For authenticated providers
    
    # Prompt structure
    system_prompt: str = ""
    assistant_instruction: str = ""
    
    # Generation parameters
    temperature: float = DEFAULT_LLM_CONFIG['temperature']
    max_tokens: int = DEFAULT_LLM_CONFIG['max_tokens']
    top_p: float = DEFAULT_LLM_CONFIG['top_p']
    top_k: Optional[int] = DEFAULT_LLM_CONFIG['top_k']
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: List[str] = field(default_factory=list)
    
    # Response handling
    response_format: str = DEFAULT_LLM_CONFIG['response_format']
    json_schema: Optional[Dict] = None  # For structured output
    
    # Execution settings
    timeout: int = DEFAULT_LLM_CONFIG['timeout']
    retry_count: int = DEFAULT_LLM_CONFIG['retry_count']
    retry_delay: float = DEFAULT_LLM_CONFIG['retry_delay']
    stream: bool = DEFAULT_LLM_CONFIG['stream']
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.provider not in LLM_PROVIDERS:
            raise ValueError(f"Unknown provider: {self.provider}. "
                           f"Available: {list(LLM_PROVIDERS.keys())}")
        
        if self.response_format not in RESPONSE_FORMATS:
            raise ValueError(f"Unknown response format: {self.response_format}. "
                           f"Available: {RESPONSE_FORMATS}")
    
    @property
    def effective_model(self) -> str:
        """Get the model to use, falling back to provider default."""
        if self.model:
            return self.model
        return LLM_PROVIDERS[self.provider]['default_model']
    
    @property
    def effective_base_url(self) -> str:
        """Get the base URL, with optional override."""
        if self.endpoint_url:
            return self.endpoint_url.rstrip('/')
        return LLM_PROVIDERS[self.provider]['base_url']
    
    def to_provider_params(self) -> Dict[str, Any]:
        """Convert to provider-specific generation parameters."""
        params = {
            'model': self.effective_model,
            'temperature': self.temperature,
        }
        
        # Provider-specific parameter names
        if self.provider == 'ollama':
            params['options'] = {
                'num_predict': self.max_tokens,
                'top_p': self.top_p,
                'top_k': self.top_k,
                'temperature': self.temperature,
            }
            if self.stop_sequences:
                params['options']['stop'] = self.stop_sequences
        else:
            # OpenAI-compatible format
            params['max_tokens'] = self.max_tokens
            params['top_p'] = self.top_p
            if self.stop_sequences:
                params['stop'] = self.stop_sequences
            if self.frequency_penalty:
                params['frequency_penalty'] = self.frequency_penalty
            if self.presence_penalty:
                params['presence_penalty'] = self.presence_penalty
        
        return params
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMConfig':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    @classmethod
    def from_concrete(cls, concrete: Dict[str, Any], context: Dict[str, Any] = None) -> 'LLMConfig':
        """
        Create LLMConfig from concrete implementation and context.
        
        Merges llm_config from concrete with context overrides.
        """
        context = context or {}
        
        # Start with defaults from concrete's llm_config
        config_data = concrete.get('llm_config', {}).copy()
        
        # Override with top-level concrete fields
        for key in ['provider', 'model', 'system_prompt', 'temperature', 'max_tokens']:
            if key in concrete:
                config_data[key] = concrete[key]
        
        # Override with context
        for key in cls.__dataclass_fields__:
            if key in context:
                config_data[key] = context[key]
        
        return cls.from_dict(config_data)
