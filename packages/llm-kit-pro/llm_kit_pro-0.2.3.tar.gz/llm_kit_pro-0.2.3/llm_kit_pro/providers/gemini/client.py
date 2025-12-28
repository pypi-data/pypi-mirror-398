import asyncio
from typing import Any, Dict, List, Optional

from llm_kit_pro.core.base import BaseLLMClient
from llm_kit_pro.core.inputs import LLMFile
from llm_kit_pro.providers.gemini.config import GeminiConfig

try:
    import google.genai as genai
    from google.genai import types
except ImportError as e:
    raise ImportError(
        "Gemini support is not installed.\n"
        "Install it with:\n"
        "  pip install llm-kit-pro[gemini]"
    ) from e



class GeminiClient(BaseLLMClient):
    def __init__(self, config: GeminiConfig):
        self.config = config
        self._client = self._create_client()

    def _create_client(self):
        return genai.Client(api_key=self.config.api_key)

    async def generate_text(
        self,
        prompt: str,
        *,
        files: Optional[List[LLMFile]] = None,
        **kwargs: Any,
    ) -> str:
        contents = self._build_contents(prompt, files)

        response = await asyncio.to_thread(
            self._client.models.generate_content,
            model=self.config.model,
            contents=contents,
            config={
                "temperature": kwargs.get(
                    "temperature", self.config.temperature
                ),
            },
        )

        return response.text

    async def generate_json(
        self,
        prompt: str,
        schema: Dict[str, Any],
        *,
        files: Optional[List[LLMFile]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        contents = self._build_contents(prompt, files)

        response = await asyncio.to_thread(
            self._client.models.generate_content,
            model=self.config.model,
            contents=contents,
            config={
                "temperature": kwargs.get(
                    "temperature", self.config.temperature
                ),
                "response_mime_type": "application/json",
                "response_schema": schema,
            },
        )

        return response.parsed
        
    def _build_contents(
        self, prompt: str, files: Optional[List[LLMFile]]
    ) -> list[types.Part]:
        parts: list[types.Part] = [
            types.Part.from_text(text=prompt)
        ]

        if files:
            for file in files:
                parts.append(
                    types.Part.from_bytes(
                        data=file.content,
                        mime_type=file.mime_type,
                    )
                )

        return parts

