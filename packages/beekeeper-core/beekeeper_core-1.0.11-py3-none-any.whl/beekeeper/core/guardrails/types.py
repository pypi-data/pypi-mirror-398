from typing import Any, Optional

from pydantic import BaseModel, Field


class GuardrailResponse(BaseModel):
    """Guardrail response."""

    text: str = Field(..., description="Generated text response")
    action: Optional[str] = Field(
        default=None, description="Action taken by the guardrail"
    )
    raw: Optional[Any] = Field(default=None)
