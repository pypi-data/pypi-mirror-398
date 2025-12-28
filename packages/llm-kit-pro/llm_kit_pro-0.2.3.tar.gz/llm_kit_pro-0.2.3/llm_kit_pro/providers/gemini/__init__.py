from llm_kit_pro.core.registry import register_provider
from llm_kit_pro.providers.gemini.client import GeminiClient

register_provider("gemini", GeminiClient)

__all__ = ["GeminiClient"]
