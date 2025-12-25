from unittest.mock import MagicMock, patch

import pytest

from llm_kit.core.inputs import LLMFile
from llm_kit.providers.gemini.client import GeminiClient
from llm_kit.providers.gemini.config import GeminiConfig


@pytest.mark.asyncio
async def test_generate_text_without_files():
    mock_response = MagicMock(text="Hello world")

    mock_models = MagicMock()
    mock_models.generate_content = MagicMock(return_value=mock_response)

    mock_client = MagicMock()
    mock_client.models = mock_models

    with patch.object(
        GeminiClient,
        "_create_client",
        return_value=mock_client,
    ):
        client = GeminiClient(GeminiConfig(api_key="fake-key"))

        result = await client.generate_text("Say hello")

        assert result == "Hello world"


@pytest.mark.asyncio
async def test_generate_text_with_file():
    fake_pdf = LLMFile(
        content=b"%PDF-1.4 fake pdf",
        mime_type="application/pdf",
        filename="bill.pdf",
    )

    mock_response = MagicMock(text="Bill summary")
    mock_uploaded_file = MagicMock()

    mock_models = MagicMock()
    mock_models.generate_content = MagicMock(return_value=mock_response)

    mock_files = MagicMock()
    mock_files.upload = MagicMock(return_value=mock_uploaded_file)

    mock_client = MagicMock()
    mock_client.models = mock_models
    mock_client.files = mock_files

    with patch.object(
        GeminiClient,
        "_create_client",
        return_value=mock_client,
    ):
        client = GeminiClient(GeminiConfig(api_key="fake-key"))

        result = await client.generate_text(
            "Summarize this bill",
            files=[fake_pdf],
        )

        assert result == "Bill summary"


@pytest.mark.asyncio
async def test_generate_json():
    mock_response = MagicMock(parsed={"amount": 123.45})

    mock_models = MagicMock()
    mock_models.generate_content = MagicMock(return_value=mock_response)

    mock_client = MagicMock()
    mock_client.models = mock_models

    with patch.object(
        GeminiClient,
        "_create_client",
        return_value=mock_client,
    ):
        client = GeminiClient(GeminiConfig(api_key="fake-key"))

        result = await client.generate_json(
            prompt="Extract amount",
            schema={
                "type": "object",
                "properties": {"amount": {"type": "number"}},
            },
        )

        assert result == {"amount": 123.45}
