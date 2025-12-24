"""
LLM Runtime Module

Provides LLMRuntime (RuntimeExecutor subclass) for executing LLM prompts
as part of the PTR polyglot runtime system.
"""

import json
import logging
from dataclasses import asdict
from typing import Any, Callable, Dict, List, Optional

from mcard import MCard
from mcard.ptr.core.runtime import RuntimeExecutor
from mcard.ptr.core.monads import IO, Either, Left, Right
from .config import LLMConfig, LLM_PROVIDERS, DEFAULT_PROVIDER
from .providers import LLMProvider, OllamaProvider, MLCLLMProvider


# ─────────────────────────────────────────────────────────────────────────────
# Provider Factory
# ─────────────────────────────────────────────────────────────────────────────

def get_provider(
    provider_name: str = DEFAULT_PROVIDER,
    base_url: str = None,
    timeout: int = 120
) -> LLMProvider:
    """
    Get an LLM provider instance by name.
    
    Args:
        provider_name: Provider identifier ('ollama', 'lmstudio', 'openai', etc.)
        base_url: Optional override for the provider's base URL
        timeout: Request timeout in seconds
        
    Returns:
        LLMProvider instance
    """
    providers = {
        'ollama': lambda: OllamaProvider(base_url, timeout),
        'mlc-llm': lambda: MLCLLMProvider(base_url, timeout),
        # Future: 'lmstudio': lambda: LMStudioProvider(base_url, timeout),
        # Future: 'openai': lambda: OpenAIProvider(base_url, timeout, api_key),
    }
    
    factory = providers.get(provider_name)
    if not factory:
        raise ValueError(f"Unknown provider: {provider_name}. Available: {list(providers.keys())}")
    
    return factory()


# ─────────────────────────────────────────────────────────────────────────────
# LLM Runtime Executor
# ─────────────────────────────────────────────────────────────────────────────

class LLMRuntime(RuntimeExecutor):
    """
    LLM runtime executor for the PTR polyglot runtime system.
    
    Executes LLM prompts via configurable providers (Ollama, LMStudio, OpenAI, etc.)
    and integrates with the standard RuntimeFactory pattern.
    
    Usage in PCard concrete section:
        concrete:
          runtime: llm
          provider: ollama
          model: gemma3:27b
          llm_config:
            system_prompt: "You are a helpful assistant."
            temperature: 0.7
            max_tokens: 1024
    """
    
    runtime_name = "llm"
    
    def __init__(self, provider_name: str = DEFAULT_PROVIDER):
        super().__init__()
        self.provider_name = provider_name
        self._provider: Optional[LLMProvider] = None
    
    @property
    def provider(self) -> LLMProvider:
        """Lazy-load provider on first access."""
        if self._provider is None:
            self._provider = get_provider(self.provider_name)
        return self._provider
    
    def execute(
        self, 
        concrete_impl: Dict[str, Any], 
        target: MCard, 
        context: Dict[str, Any]
    ) -> Any:
        """
        Execute LLM prompt based on concrete implementation.
        
        Args:
            concrete_impl: Concrete section from PCard containing llm_config
            target: Target MCard containing the prompt/input
            context: Execution context with optional overrides
            
        Returns:
            LLM response (string or structured data based on response_format)
        """
        # Build configuration from concrete and context
        config = LLMConfig.from_concrete(concrete_impl, context)
        
        # Update provider if different from init
        if config.provider != self.provider_name:
            self._provider = get_provider(config.provider, config.endpoint_url, config.timeout)
        
        # Get prompt from target
        prompt = self._extract_prompt(target, context)
        
        # Execute via appropriate method
        if config.system_prompt:
            result = self._execute_chat(prompt, config)
        else:
            result = self._execute_completion(prompt, config)
        
        # Handle result
        if result.is_left():
            return f"Error: {result.value}"
        
        return self._format_response(result.value, config)
    
    def _extract_prompt(self, target: MCard, context: Dict) -> str:
        """Extract prompt from target MCard."""
        content = target.get_content()
        if isinstance(content, bytes):
            return content.decode('utf-8')
        return str(content)
    
    def _execute_completion(self, prompt: str, config: LLMConfig) -> Either[str, str]:
        """Execute text completion."""
        params = config.to_provider_params()
        return self.provider.complete(prompt, params)
    
    def _execute_chat(self, prompt: str, config: LLMConfig) -> Either[str, Dict]:
        """Execute chat completion with system prompt."""
        messages = []
        
        # Add system prompt
        if config.system_prompt:
            messages.append({
                "role": "system",
                "content": config.system_prompt
            })
        
        # Add user message
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Add assistant instruction (prefill) if provided
        if config.assistant_instruction:
            messages.append({
                "role": "assistant",
                "content": config.assistant_instruction
            })
        
        params = config.to_provider_params()
        return self.provider.chat(messages, params)
    
    def _format_response(self, response: Any, config: LLMConfig) -> Any:
        """Format response based on response_format setting."""
        # Extract content from chat response
        if isinstance(response, dict):
            content = response.get('content', response)
        else:
            content = response
        
        # Format based on config
        if config.response_format == 'json':
            try:
                # Try to parse as JSON
                if isinstance(content, str):
                    # Find JSON in response
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    if start >= 0 and end > start:
                        return json.loads(content[start:end])
                return content
            except json.JSONDecodeError:
                return content
        
        return content
    
    def validate_environment(self) -> bool:
        """Check if the LLM provider is available."""
        try:
            return self.provider.validate_connection()
        except Exception:
            return False
    
    def get_runtime_status(self) -> Dict[str, Any]:
        """Get LLM runtime status with provider info."""
        try:
            available = self.validate_environment()
            models = []
            
            if available:
                models_result = self.provider.list_models()
                if models_result.is_right():
                    models = models_result.value
            
            return {
                'available': available,
                'version': f"{self.provider_name} ({len(models)} models)" if available else None,
                'provider': self.provider_name,
                'models': models,
                'command': 'ollama' if self.provider_name == 'ollama' else self.provider_name,
                'details': f"LLM Runtime via {self.provider_name}"
            }
        except Exception as e:
            return {
                'available': False,
                'version': None,
                'provider': self.provider_name,
                'models': [],
                'command': self.provider_name,
                'details': f"Error: {e}"
            }


# ─────────────────────────────────────────────────────────────────────────────
# Monadic Interface Functions
# ─────────────────────────────────────────────────────────────────────────────

def prompt_monad(
    prompt: str,
    config: LLMConfig = None,
    **kwargs
) -> IO[Either[str, str]]:
    """
    Create a monadic LLM completion execution.
    
    Returns IO[Either[Error, Response]] for functional composition.
    
    Usage:
        result = prompt_monad("Explain monads", temperature=0.5).unsafe_run()
        if result.is_right():
            print(result.value)
    
    Args:
        prompt: The input prompt
        config: Optional LLMConfig (uses defaults if not provided)
        **kwargs: Override config parameters
        
    Returns:
        IO[Either[str, str]]: Monadic wrapper around the LLM call
    """
    if config is None:
        config = LLMConfig(**kwargs) if kwargs else LLMConfig()
    elif kwargs:
        # Merge kwargs into config
        config_dict = config.to_dict()
        config_dict.update(kwargs)
        config = LLMConfig.from_dict(config_dict)
    
    def run() -> Either[str, str]:
        try:
            runtime = LLMRuntime(config.provider)
            result = runtime._execute_completion(prompt, config)
            return result
        except Exception as e:
            return Left(f"LLM execution failed: {e}")
    
    return IO(run)


def chat_monad(
    messages: List[Dict[str, str]] = None,
    prompt: str = None,
    system_prompt: str = "",
    config: LLMConfig = None,
    **kwargs
) -> IO[Either[str, Dict]]:
    """
    Create a monadic LLM chat execution.
    
    Returns IO[Either[Error, Response]] for functional composition.
    
    Usage:
        result = chat_monad(
            prompt="What is Python?",
            system_prompt="You are a programming tutor.",
            model="llama3:latest"
        ).unsafe_run()
        
        if result.is_right():
            print(result.value['content'])
    
    Args:
        messages: Optional list of message dicts (overrides prompt/system_prompt)
        prompt: User prompt (used if messages not provided)
        system_prompt: System prompt (used if messages not provided)
        config: Optional LLMConfig
        **kwargs: Override config parameters
        
    Returns:
        IO[Either[str, Dict]]: Monadic wrapper around the chat call
    """
    # Build config
    kwargs.setdefault('system_prompt', system_prompt)
    
    if config is None:
        config = LLMConfig(**kwargs) if kwargs else LLMConfig()
    elif kwargs:
        config_dict = config.to_dict()
        config_dict.update(kwargs)
        config = LLMConfig.from_dict(config_dict)
    
    # Build messages
    if messages is None:
        messages = []
        if config.system_prompt:
            messages.append({"role": "system", "content": config.system_prompt})
        if prompt:
            messages.append({"role": "user", "content": prompt})
    
    def run() -> Either[str, Dict]:
        try:
            provider = get_provider(config.provider, config.endpoint_url, config.timeout)
            params = config.to_provider_params()
            return provider.chat(messages, params)
        except Exception as e:
            return Left(f"LLM chat failed: {e}")
    
    return IO(run)
