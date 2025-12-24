"""
Provider registry for LLM backends
Clean, extensible, no over-engineering
"""

import os
from typing import Dict, Any, Protocol
import litellm


class ProviderConfig(Protocol):
    """Protocol for provider configurations"""
    def get_litellm_params(self) -> Dict[str, Any]:
        """Return params for litellm.completion()"""
        ...


class CerebrasProvider:
    """Cerebras Cloud provider (DEFAULT)"""
    
    def __init__(self, model: str = "cerebras/llama3.1-8b", temperature: float = 0.7, api_key: str = None, api_base: str = None):
        self.model = model
        self.temperature = temperature
        self.api_key = api_key
        self.api_base = api_base or "https://api.cerebras.ai/v1"
    
    def get_litellm_params(self) -> Dict[str, Any]:
        params = {
            "model": self.model,
            "temperature": self.temperature,
            "api_base": self.api_base,
            "custom_llm_provider": "cerebras",
            "extra_headers": {"X-Cerebras-3rd-Party-Integration": "litellm"}
        }
        if self.api_key:
            params["api_key"] = self.api_key
        return params


class OpenAIProvider:
    """OpenAI provider"""
    
    def __init__(self, model: str = "gpt-3.5-turbo", temperature: float = 0.7, api_key: str = None, api_base: str = None):
        self.model = model
        self.temperature = temperature
        self.api_key = api_key
        self.api_base = api_base
    
    def get_litellm_params(self) -> Dict[str, Any]:
        params = {
            "model": self.model,
            "temperature": self.temperature
        }
        if self.api_key:
            params["api_key"] = self.api_key
        if self.api_base:
            params["api_base"] = self.api_base
        return params


class AnthropicProvider:
    """Anthropic Claude provider"""
    
    def __init__(self, model: str = "claude-3-5-sonnet-20241022", temperature: float = 0.7, api_key: str = None, api_base: str = None):
        self.model = model
        self.temperature = temperature
        self.api_key = api_key
        self.api_base = api_base
    
    def get_litellm_params(self) -> Dict[str, Any]:
        params = {
            "model": self.model,
            "temperature": self.temperature
        }
        if self.api_key:
            params["api_key"] = self.api_key
        if self.api_base:
            params["api_base"] = self.api_base
        return params


class GeminiProvider:
    """Google Gemini provider"""
    
    def __init__(self, model: str = "gemini/gemini-1.5-flash", temperature: float = 0.7, api_key: str = None, api_base: str = None):
        self.model = model
        self.temperature = temperature
        self.api_key = api_key
        self.api_base = api_base
    
    def get_litellm_params(self) -> Dict[str, Any]:
        params = {
            "model": self.model,  # litellm expects "gemini/..." for some, but typically just model name if provider is set, 
                                  # but here we follow litellm conventions. "gemini/gemini-1.5-flash" is standard.
            "temperature": self.temperature
        }
        if self.api_key:
            params["api_key"] = self.api_key
        if self.api_base:
            params["api_base"] = self.api_base
        return params


class OpenAICompatibleProvider:
    """
    Generic OpenAI-compatible endpoint
    For local models (LM Studio, vLLM, Ollama with OpenAI compat, etc.)
    """
    
    def __init__(
        self,
        model: str = "local-model",
        api_base: str ="http://localhost:8000/v1",
        temperature: float = 0.7,
        api_key: str = "not-needed"
    ):
        self.model = model
        self.api_base = api_base
        self.temperature = temperature
        self.api_key = api_key
    
    def get_litellm_params(self) -> Dict[str, Any]:
        return {
            "model": f"openai/{self.model}",  # LiteLLM uses openai/ prefix for custom endpoints
            "api_base": self.api_base,
            "api_key": self.api_key,
            "temperature": self.temperature
        }


# Provider Registry
PROVIDER_REGISTRY: Dict[str, type] = {
    "cerebras": CerebrasProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "local": OpenAICompatibleProvider,  # For OpenAI-compatible local models
}


def get_provider(provider_name: str, **kwargs) -> ProviderConfig:
    """
    Factory function to get provider instance
    
    Examples:
        get_provider("cerebras", model="cerebras/llama3.1-70b")
        get_provider("openai", model="gpt-4")
        get_provider("local", api_base="http://localhost:1234/v1", model="llama-3.2")
    """
    provider_class = PROVIDER_REGISTRY.get(provider_name)
    
    if not provider_class:
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            f"Available: {', '.join(PROVIDER_REGISTRY.keys())}"
        )
    
    return provider_class(**kwargs)
