import base64
import json
from typing import Any, Dict, List, Optional

from llm_kit_pro.core.inputs import LLMFile
from llm_kit_pro.providers.bedrock.adapters.base import BedrockModelAdapter
from llm_kit_pro.providers.bedrock.constants import ANTHROPIC_BEDROCK_VERSION


class ClaudeAdapter(BedrockModelAdapter):
    # ---------- internal helpers ----------

    def _file_to_content_block(self, file: LLMFile) -> Dict[str, Any]:
        encoded = base64.b64encode(file.content).decode("utf-8")

        if file.mime_type.startswith("image/"):
            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": file.mime_type,
                    "data": encoded,
                },
            }

        if file.mime_type == "application/pdf":
            return {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": encoded,
                },
            }

        raise ValueError(
            f"Unsupported file type for Claude on Bedrock: {file.mime_type}"
        )

    def _build_request(
        self,
        prompt: str,
        *,
        files: Optional[List[LLMFile]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        temperature = kwargs.get("temperature")
        max_tokens = kwargs.get("max_tokens", 1024)

        content_blocks: List[Dict[str, Any]] = [
            {"type": "text", "text": prompt}
        ]

        if files:
            for file in files:
                content_blocks.append(self._file_to_content_block(file))

        payload: Dict[str, Any] = {
            "anthropic_version": ANTHROPIC_BEDROCK_VERSION,
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": content_blocks,
                }
            ],
        }

        if temperature is not None:
            payload["temperature"] = temperature

        return {
            "modelId": self.model_id,
            "contentType": "application/json",
            "accept": "application/json",
            "body": json.dumps(payload),
        }

    # ---------- public API ----------

    def build_text_request(
        self,
        prompt: str,
        *,
        files: Optional[List[LLMFile]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        return self._build_request(prompt, files=files, **kwargs)

    def build_json_request(
        self,
        prompt: str,
        schema: Dict[str, Any],
        *,
        files: Optional[List[LLMFile]] = None,
        inject_schema: bool = True,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        if inject_schema:
            schema_prompt = (
                f"{prompt}\n\n"
                f"Return ONLY valid JSON matching this schema:\n"
                f"{json.dumps(schema)}"
            )
        else:
            schema_prompt = prompt
        return self._build_request(schema_prompt, files=files, inject_schema=inject_schema, **kwargs)

    def parse_response(self, response: Dict[str, Any]) -> str:
        body = json.loads(response["body"].read())
        return body["content"][0]["text"]
