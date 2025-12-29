"""User message model for the Connexity SDK.

This module defines `UserMessage`, representing a user-authored message in the
conversation timeline. It may optionally mark whether the message occurred as an
interruption.
"""

from __future__ import annotations

from typing import Any

from connexity.calls.messages.base_message import BaseMessage


class UserMessage(BaseMessage):
    """Represents a user message in the conversation timeline."""

    def __init__(
        self,
        content: str,
        seconds_from_start: float | None = None,
        is_interruption: bool | None = None,
    ) -> None:
        """Initialize a user message.

        Args:
            content: Message content.
            seconds_from_start: Offset in seconds from the start of the session.
            is_interruption: Whether this user message is considered an
                interruption (optional).
        """
        super().__init__("user", content, seconds_from_start)
        self.is_interruption: bool | None = is_interruption

    def to_dict(self) -> dict[str, Any]:
        """Serialize the user message to a JSON-friendly dict.

        Returns:
            Dictionary representation of this user message.
        """
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "seconds_from_start": self.seconds_from_start,
            "is_interruption": self.is_interruption,
        }
