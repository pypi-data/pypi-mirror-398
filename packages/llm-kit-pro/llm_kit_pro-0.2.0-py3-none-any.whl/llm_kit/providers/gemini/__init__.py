from llm_kit.core.registry import register_provider
from llm_kit.providers.gemini.client import GeminiClient

register_provider("gemini", GeminiClient)

__all__ = ["GeminiClient"]
