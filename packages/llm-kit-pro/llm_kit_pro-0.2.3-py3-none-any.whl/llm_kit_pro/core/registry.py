from typing import TYPE_CHECKING, Dict, Literal, Type, overload

from llm_kit_pro.core.base import BaseLLMClient

# ---------------- runtime registry ----------------

_PROVIDER_REGISTRY: Dict[str, Type[BaseLLMClient]] = {}


def register_provider(name: str, client: Type[BaseLLMClient]) -> None:
    _PROVIDER_REGISTRY[name] = client


# ---------------- typing only (NO runtime imports) ----------------

if TYPE_CHECKING:
    from llm_kit_pro.providers.bedrock.client import BedrockClient
    from llm_kit_pro.providers.gemini.client import GeminiClient

ProviderName = Literal["bedrock", "gemini"]


@overload
def get_provider(name: Literal["bedrock"]) -> Type["BedrockClient"]: ...
@overload
def get_provider(name: Literal["gemini"]) -> Type["GeminiClient"]: ...


def get_provider(name: ProviderName) -> Type[BaseLLMClient]:
    if name not in _PROVIDER_REGISTRY:
        raise ValueError(f"Provider '{name}' not registered")
    return _PROVIDER_REGISTRY[name]
