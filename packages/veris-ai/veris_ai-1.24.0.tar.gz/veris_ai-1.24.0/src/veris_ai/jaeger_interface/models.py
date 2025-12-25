from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "Tag",
    "Process",
    "Span",
    "Trace",
    "SearchResponse",
    "GetTraceResponse",
]


class Tag(BaseModel):
    """A Jaeger tag key/value pair."""

    key: str
    value: Any
    type: str | None = None  # Jaeger uses an optional *type* field in v1


class Process(BaseModel):
    """Represents the *process* section of a Jaeger trace."""

    serviceName: str = Field(alias="serviceName")  # noqa: N815
    tags: list[Tag] | None = None


class Span(BaseModel):
    """Represents a single Jaeger span."""

    traceID: str  # noqa: N815
    spanID: str  # noqa: N815
    operationName: str  # noqa: N815
    startTime: int  # noqa: N815
    duration: int
    tags: list[Tag] | None = None
    references: list[dict[str, Any]] | None = None
    processID: str | None = None  # noqa: N815

    model_config = ConfigDict(extra="allow")


class Trace(BaseModel):
    """A full Jaeger trace as returned by the Query API."""

    traceID: str  # noqa: N815
    spans: list[Span]
    process: Process | dict[str, Process] | None = None
    warnings: list[str] | None = None

    model_config = ConfigDict(extra="allow")


class _BaseResponse(BaseModel):
    data: list[Trace] | Trace | None = None
    errors: list[str] | None = None

    # Allow any additional keys returned by Jaeger so that nothing gets
    # silently dropped if the backend adds new fields we don't know about.

    model_config = ConfigDict(extra="allow")


class SearchResponse(_BaseResponse):
    """Response model for *search* or *find traces* requests."""

    total: int | None = None
    limit: int | None = None


class GetTraceResponse(_BaseResponse):
    """Response model for *get trace by id* requests."""

    # Same as base but alias for clarity
