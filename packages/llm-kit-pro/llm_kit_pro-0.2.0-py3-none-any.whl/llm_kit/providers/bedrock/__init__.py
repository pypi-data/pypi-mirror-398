from llm_kit.core.registry import register_provider
from llm_kit.providers.bedrock.client import BedrockClient

register_provider("bedrock", BedrockClient)

__all__ = ["BedrockClient"]
