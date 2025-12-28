from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from llm_kit_pro.core.inputs import LLMFile


class BaseLLMClient(ABC):
    """
    Base contract for all LLM providers.

    Providers must implement text and structured generation.
    Files (PDFs, images, etc.) are optional first-class inputs.
    """

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        *,
        files: Optional[List[LLMFile]] = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate free-form text output.

        Args:
            prompt: User prompt / instruction.
            files: Optional list of attached files (PDF, image, etc.).
            **kwargs: Provider-specific options (model, temperature, etc.).

        Returns:
            Generated text.
        """
        raise NotImplementedError

    @abstractmethod
    async def generate_json(
        self,
        prompt: str,
        schema: Dict[str, Any],
        *,
        files: Optional[List[LLMFile]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output matching the provided schema.

        Args:
            prompt: User prompt / instruction.
            schema: JSON schema describing expected output.
            files: Optional list of attached files (PDF, image, etc.).
            **kwargs: Provider-specific options (model, temperature, etc.).

        Returns:
            Parsed JSON output.
        """
        raise NotImplementedError
