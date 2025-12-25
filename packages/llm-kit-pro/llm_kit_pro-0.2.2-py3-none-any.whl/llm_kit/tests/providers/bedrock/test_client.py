import json
from unittest.mock import MagicMock, patch

import pytest

from llm_kit.core.inputs import LLMFile
from llm_kit.providers.bedrock.client import BedrockClient
from llm_kit.providers.bedrock.config import BedrockConfig


@pytest.mark.asyncio
async def test_generate_text_without_files():
    # Mock Bedrock response
    mock_body = MagicMock()
    mock_body.read.return_value = json.dumps({
        "content": [{"text": "Hello from Claude"}]
    }).encode()

    mock_response = {"body": mock_body}

    mock_runtime = MagicMock()
    mock_runtime.invoke_model = MagicMock(return_value=mock_response)

    with patch("boto3.client", return_value=mock_runtime):
        client = BedrockClient(
            BedrockConfig(
                access_key="fake",
                secret_key="fake",
                region="us-east-1",
                model="anthropic.claude-3-sonnet-20240229-v1:0",
            )
        )

        result = await client.generate_text("Say hello")

        assert result == "Hello from Claude"


@pytest.mark.asyncio
async def test_generate_text_with_file():
    fake_pdf = LLMFile(
        content=b"%PDF-1.4 fake pdf",
        mime_type="application/pdf",
        filename="bill.pdf",
    )

    mock_body = MagicMock()
    mock_body.read.return_value = json.dumps({
        "content": [{"text": "Bill summary"}]
    }).encode()

    mock_response = {"body": mock_body}

    mock_runtime = MagicMock()
    mock_runtime.invoke_model = MagicMock(return_value=mock_response)

    with patch("boto3.client", return_value=mock_runtime):
        client = BedrockClient(
            BedrockConfig(
                access_key="fake",
                secret_key="fake",
                region="us-east-1",
                model="global.anthropic.claude-sonnet-4-5-20250929-v1:0",
            )
        )

        result = await client.generate_text(
            "Summarize this bill",
            files=[fake_pdf],
        )

        assert result == "Bill summary"


@pytest.mark.asyncio
async def test_generate_json_with_extraction():
    # Claude returns text WITH extra prose inside Bedrock envelope
    mock_body = MagicMock()
    mock_body.read.return_value = json.dumps({
        "content": [
            {
                "text": (
                    "Sure! Here is the extracted data:\n\n"
                    "{ \"amount\": 123.45 }\n"
                )
            }
        ]
    }).encode()

    mock_response = {"body": mock_body}

    mock_runtime = MagicMock()
    mock_runtime.invoke_model = MagicMock(return_value=mock_response)

    with patch("boto3.client", return_value=mock_runtime):
        client = BedrockClient(
            BedrockConfig(
                access_key="fake",
                secret_key="fake",
                region="us-east-1",
                model="anthropic.claude-3-sonnet-20240229-v1:0",
            )
        )

        result = await client.generate_json(
            prompt="Extract amount",
            schema={
                "type": "object",
                "properties": {"amount": {"type": "number"}},
            },
        )

        assert result == {"amount": 123.45}
