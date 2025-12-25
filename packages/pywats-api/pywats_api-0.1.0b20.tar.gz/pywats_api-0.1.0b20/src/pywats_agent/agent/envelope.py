from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class ToolResultEnvelope(BaseModel):
    """LLM-safe tool result.

    This is the *only* thing that should be sent back to the model.

    - `data_key` is a handle to the full data stored out-of-band.
    - `preview` is bounded to avoid context inflation.
    """

    ok: bool = Field(description="Whether tool execution succeeded")
    summary: str = Field(description="Human-readable summary (bounded)")

    data_key: Optional[str] = Field(
        default=None,
        description="Handle to full data in a DataStore; never inline bulk data into the LLM",
    )

    viz_key: Optional[str] = Field(
        default=None,
        description="Handle to visualization payload in a DataStore (UI sidecar; never inline into the LLM)",
    )

    preview: Optional[dict[str, Any]] = Field(
        default=None,
        description="Bounded preview of data (rows, schema) suitable for LLM context",
    )

    metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Counts, sizes, truncation flags",
    )

    warnings: list[str] = Field(default_factory=list)
    error: Optional[str] = Field(default=None)
