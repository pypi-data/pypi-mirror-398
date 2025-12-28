from llm_kit_pro.core.registry import register_provider
from llm_kit_pro.providers.bedrock.client import BedrockClient

register_provider("bedrock", BedrockClient)

__all__ = ["BedrockClient"]
