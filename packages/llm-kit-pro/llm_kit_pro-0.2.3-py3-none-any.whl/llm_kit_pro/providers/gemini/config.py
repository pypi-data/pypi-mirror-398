from pydantic import BaseModel, Field


class GeminiConfig(BaseModel):
    api_key: str = Field(..., description="Gemini API key")
    model: str = Field(default="gemini-2.5-flash")
    temperature: float = Field(default=0.2)
