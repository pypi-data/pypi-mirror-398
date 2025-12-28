import asyncio
from typing import Any, Dict

from llm_kit_pro.core.json_utils import extract_json

try:
    import boto3
except ImportError as e:
    raise ImportError(
        "Bedrock support is not installed.\n"
        "Install it with:\n"
        "  pip install llm-kit-pro[bedrock]"
    ) from e

from llm_kit_pro.core.base import BaseLLMClient
from llm_kit_pro.providers.bedrock.adapters.claude import ClaudeAdapter
from llm_kit_pro.providers.bedrock.config import BedrockConfig


class BedrockClient(BaseLLMClient):
    def __init__(self, config: BedrockConfig):
        self.config = config
        self._runtime = boto3.client(
            "bedrock-runtime",
            aws_access_key_id=config.access_key,
            aws_secret_access_key=config.secret_key,
            region_name=config.region,
        )

        self._adapter = self._resolve_adapter()

    def _resolve_adapter(self):
        if self.config.model.startswith("anthropic.") or self.config.model.startswith("global.anthropic."):
            return ClaudeAdapter(self.config.model)

        raise ValueError(f"Unsupported Bedrock model: {self.config.model}")

    async def generate_text(self, prompt: str, **kwargs: Any) -> str:
        request = self._adapter.build_text_request(prompt, **kwargs)

        response = await asyncio.to_thread(
            self._runtime.invoke_model,
            **request
        )

        return self._adapter.parse_response(response)

    async def generate_json(
        self,
        prompt: str,
        schema: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        request = self._adapter.build_json_request(prompt, schema, **kwargs)

        response = await asyncio.to_thread(
            self._runtime.invoke_model,
            **request
        )

        raw = self._adapter.parse_response(response)
        return extract_json(raw)
