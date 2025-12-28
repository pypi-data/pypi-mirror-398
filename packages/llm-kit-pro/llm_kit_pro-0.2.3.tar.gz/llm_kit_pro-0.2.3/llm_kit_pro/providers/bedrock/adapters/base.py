from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from llm_kit_pro.core.inputs import LLMFile


class BedrockModelAdapter(ABC):
    def __init__(self, model_id: str):
        self.model_id = model_id

    @abstractmethod
    def build_text_request(
        self,
        prompt: str,
        *,
        files: Optional[List[LLMFile]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def build_json_request(
        self,
        prompt: str,
        schema: Dict[str, Any],
        *,
        files: Optional[List[LLMFile]] = None,
        inject_schema: bool = True,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def parse_response(self, response: Dict[str, Any]) -> Any:
        pass
