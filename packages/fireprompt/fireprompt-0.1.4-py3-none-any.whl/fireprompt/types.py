# fireprompt/types.py
# SPDX-License-Identifier: MIT

# imports
from typing import Any
from pydantic import Field
from pydantic import BaseModel


class LLMConfig(BaseModel):
    """LLM configuration."""
    max_tokens: int | None = Field(None, ge=0)
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    top_p: float | None = Field(None, ge=0.0, le=1.0)
    extra: dict[str, Any] | None = Field(None, description="provider-specific")


class LLMConfigPreset:
    """Pre-configured LLM settings for common use cases."""
    DEFAULT = LLMConfig(temperature=0.7)
    CREATIVE = LLMConfig(temperature=0.9, top_p=0.95)
    PRECISE = LLMConfig(temperature=0.3, top_p=0.9)
    DETERMINISTIC = LLMConfig(temperature=0.0, top_p=1.0)


class LLM(BaseModel):
    """LLM model."""
    name: str
    config: LLMConfig = Field(default_factory=lambda: LLMConfigPreset.DEFAULT)
