"""Assistant message model for the Connexity SDK.

This module defines :class:`AssistantMessage`, a concrete implementation of
:class:`~connexity.calls.messages.base_message.BaseMessage` for
assistant/agent outputs.

The message can optionally include latency breakdowns and timing metrics.
"""

from __future__ import annotations

from typing import Any

from connexity.calls.messages.base_message import BaseMessage


class AssistantMessage(BaseMessage):
    """A single assistant message emitted during a call session.

    This is a specialized :class:`~connexity.calls.messages.base_message.BaseMessage`
    with additional timing and latency metadata useful for analytics.

    Args:
        content: The assistant text content.
        time_to_first_audio: Time (in seconds) from message start until the first
            audio chunk is produced, if available.
        seconds_from_start: Timestamp (in seconds) from the start of the call session.
        latency: Optional latency breakdown. When provided and truthy, it is stored
            as-is. When omitted or falsy, a default structure is used.

    Notes:
        The `latency` argument is accepted as-is when truthy. If you pass an empty
        dict (``{}``), it is treated as falsy and the default latency structure is
        used (this preserves the existing behavior).
    """

    def __init__(
        self,
        content: str,
        time_to_first_audio: float | None = None,
        seconds_from_start: float | None = None,
        latency: dict[str, float | None] | None = None,
    ):
        """Initialize an AssistantMessage."""
        super().__init__("assistant", content, seconds_from_start)

        # Optional metric: time until the assistant produces its first audio.
        self.time_to_first_audio = time_to_first_audio

        # Latency breakdown for services involved in producing this message.
        # If a truthy mapping is provided, we preserve it as-is to avoid
        # accidentally dropping caller-provided keys/values.
        if latency:
            self.latency = latency
        else:
            # Default latency structure expected by downstream consumers.
            self.latency = {"stt": None, "llm": None, "tts": None}

    def to_dict(self) -> dict[str, Any]:
        """Serialize the message to a JSON-friendly dictionary.

        Returns:
            A dictionary containing the message payload, including timing and latency
            metadata.
        """
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "seconds_from_start": self.seconds_from_start,
            "time_to_first_audio": self.time_to_first_audio,
            "latency": self.latency,
        }
