"""Message base models for the Connexity SDK.

This module defines the base `BaseMessage` class used across the SDK to
represent a single message in a conversation timeline.

Concrete message classes should extend `BaseMessage` and implement
`to_dict()`.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Any, Literal


class BaseMessage(ABC):
    """Base class for a single conversation message.

    Attributes:
        id: Unique identifier for this message.
        role: Message role (system/assistant/user/tool_call/tool_result).
        content: Text content of the message.
        seconds_from_start: Optional timestamp offset from session start.
    """

    def __init__(
        self,
        role: Literal["system", "assistant", "user", "tool_call", "tool_result"],
        content: str,
        seconds_from_start: float | None = None,
    ) -> None:
        """Initialize a BaseMessage.

        Args:
            role: Role of the message.
            content: Message content.
            seconds_from_start: Offset in seconds from the start of the session.
        """
        self.id: str = str(uuid.uuid4())
        self.role: Literal[
            "system", "assistant", "user", "tool_call", "tool_result"
        ] = role
        self.content: str = content
        self.seconds_from_start: float | None = seconds_from_start

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serialize the message to a dictionary.

        Returns:
            A JSON-serializable dictionary representation of the message.
        """
        raise NotImplementedError
