from dataclasses import dataclass
from typing import Literal, Optional


@dataclass(frozen=True)
class LLMFile:
    content: bytes
    mime_type: Literal[
        "application/pdf",
        "image/png",
        "image/jpeg",
        "text/plain",
    ]
    filename: Optional[str] = None
