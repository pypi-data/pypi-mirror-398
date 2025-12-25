"""Models for the VERIS SDK."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel


class ResponseExpectation(str, Enum):
    """Expected response behavior for tool mocking."""

    AUTO = "auto"
    REQUIRED = "required"
    NONE = "none"


class ToolCallOptions(BaseModel):
    """Options for tool call."""

    response_expectation: ResponseExpectation = ResponseExpectation.AUTO
    cache_response: bool = False
    mode: Literal["tool", "function"] = "tool"


class SimulationConfig(BaseModel):
    """Configuration for a simulation session."""

    optimized_prompt: str | None = None
