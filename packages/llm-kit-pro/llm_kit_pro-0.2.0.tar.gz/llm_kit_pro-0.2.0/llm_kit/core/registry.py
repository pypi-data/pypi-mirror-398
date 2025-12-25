from typing import Dict, Type

from llm_kit.core.base import BaseLLMClient

_PROVIDER_REGISTRY: Dict[str, Type[BaseLLMClient]] = {}

def register_provider(name: str, client: Type[BaseLLMClient]) -> None:
    _PROVIDER_REGISTRY[name] = client

def get_provider(name: str) -> Type[BaseLLMClient]:
    if name not in _PROVIDER_REGISTRY:
        raise ValueError(f"Provider '{name}' not registered")
    return _PROVIDER_REGISTRY[name]
