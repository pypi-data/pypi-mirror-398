"""Tool-result message model for the Connexity SDK.

This module defines `ToolResultMessage`, which represents the outcome of a tool
invocation (role="tool_result"). It is typically correlated back to a
`ToolCallMessage` via `tool_call_id`.
"""

from __future__ import annotations

from typing import Any

from connexity.calls.messages.base_message import BaseMessage


class ToolResultMessage(BaseMessage):
    """Represents a tool execution result in the conversation timeline."""

    def __init__(
        self,
        content: str,
        tool_call_id: str,
        seconds_from_start: float | None = None,
        result: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a tool result message.

        Args:
            content: Human-readable message describing the outcome.
            tool_call_id: Unique id for correlating this result to a tool call.
            seconds_from_start: Offset in seconds from the start of the session.
            result: Optional textual result payload.
            metadata: Optional extra structured metadata.

        Notes:
            `metadata` is stored as-is and may be None. It is only included in
            `to_dict()` when truthy (preserves current wire format).
        """
        super().__init__("tool_result", content, seconds_from_start)
        self.tool_call_id: str = tool_call_id
        self.result: str | None = result
        self.metadata: dict[str, Any] | None = metadata

    def to_dict(self) -> dict[str, Any]:
        """Serialize the tool result message to a JSON-friendly dict.

        Returns:
            Dictionary representation of this tool result message.
        """
        base_dict: dict[str, Any] = {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "seconds_from_start": self.seconds_from_start,
            "tool_call_id": self.tool_call_id,
            "result": self.result,
        }

        # Only include metadata when it is truthy.
        if self.metadata:
            base_dict["metadata"] = self.metadata

        return base_dict
