from typing import Any, Dict

from pydantic import BaseModel


class LLMResponse(BaseModel):
    provider: str
    model: str
    raw: Any


class TextResponse(LLMResponse):
    text: str


class JSONResponse(LLMResponse):
    data: Dict[str, Any]
