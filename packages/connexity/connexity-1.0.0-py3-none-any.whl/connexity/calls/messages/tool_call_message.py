"""Tool-call message model for the Connexity SDK.

This module defines `ToolCallMessage`, which represents a tool invocation request
emitted by the assistant (role="tool_call").
"""

from __future__ import annotations

from typing import Any

from connexity.calls.messages.base_message import BaseMessage


class ToolCallMessage(BaseMessage):
    """Represents a tool call request in the conversation timeline."""

    def __init__(
        self,
        content: str,
        tool_call_id: str,
        name: str,
        seconds_from_start: float | None = None,
        arguments: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a tool call message.

        Args:
            content: Human-readable description or content associated with the call.
            tool_call_id: Unique id for correlating tool calls and results.
            name: Tool/function name being invoked.
            seconds_from_start: Offset in seconds from the start of the session.
            arguments: Tool arguments payload (kept as provided; may be None).
        """
        super().__init__("tool_call", content, seconds_from_start)
        self.tool_call_id: str = tool_call_id
        self.name: str = name
        self.arguments: dict[str, Any] | None = arguments

    def to_dict(self) -> dict[str, Any]:
        """Serialize the tool call message to a JSON-friendly dict.

        Returns:
            Dictionary representation of this tool call message.
        """
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "seconds_from_start": self.seconds_from_start,
            "tool_call_id": self.tool_call_id,
            "name": self.name,
            "arguments": self.arguments,
        }
