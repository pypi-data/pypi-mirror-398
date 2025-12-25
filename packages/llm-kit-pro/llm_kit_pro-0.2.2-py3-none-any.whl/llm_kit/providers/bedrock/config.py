from typing import Optional

from pydantic import BaseModel, Field


class BedrockConfig(BaseModel):
    access_key: str = Field(..., description="AWS Access Key")
    secret_key: str = Field(..., description="AWS Secret Key")
    region: str = Field(..., description="AWS Region")
    model: str = Field(..., description="Bedrock Model ID")

    temperature: Optional[float] = Field(
        default=None,
        description="Sampling temperature (model-dependent)"
    )

    max_tokens: Optional[int] = Field(
        default=None,
        description="Maximum tokens to generate (model-dependent)"
    )
