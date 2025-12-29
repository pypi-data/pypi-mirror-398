"""Issue message model for the Connexity SDK.

This module defines `IssueMessage`, a lightweight data container used to record
issues and noteworthy issues across the pipeline (transport, services, tools,
etc.).

The model is intentionally simple and serializable via `to_dict()`.
"""

from __future__ import annotations

import uuid
from typing import Any, Literal

IssueSource = Literal[
    "transport",
    "frame_filter",
    "observer",
    "frame_processor",
    "frame_serializer",
    "switcher",
    "llm_service",
    "tts_service",
    "stt_service",
    "tool_call",
    "unknown",
]


class IssueMessage:
    """Represents a single issue/issue observed during a call session.

    Args:
        content: Human-readable description of the issue.
        source: Component that produced the issue.
        message_id: Optional upstream message identifier (if the issue pertains
            to a specific message).
        seconds_from_start: Optional timestamp offset from the start of the
            session.
        code: Optional machine-readable issue/issue code.
        metadata: Optional extra structured context.

    Attributes:
        id: Unique identifier for this issue message.
        message_id: Optional upstream message identifier.
        content: Human-readable description.
        source: Component that produced the issue.
        seconds_from_start: Optional timestamp offset from session start.
        code: Optional machine-readable code.
        metadata: Extra structured context.
    """

    def __init__(
        self,
        content: str,
        source: IssueSource,
        message_id: str | None = None,
        seconds_from_start: float | None = None,
        code: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        # Use a regular UUID for the issue message id.
        self.id: uuid.UUID = uuid.uuid4()
        self.message_id: str | None = message_id
        self.content: str = content
        self.source: IssueSource = source
        self.seconds_from_start: float | None = seconds_from_start
        self.code: str | None = code
        self.metadata: dict[str, Any] = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        """Serialize the issue message to a JSON-friendly dict.

        Returns:
            Dictionary representation of this issue.
        """
        return {
            "id": str(self.id),
            "content": self.content,
            "source": self.source,
            "seconds_from_start": self.seconds_from_start,
            "code": self.code,
            "metadata": self.metadata,
            "message_id": self.message_id,
        }
