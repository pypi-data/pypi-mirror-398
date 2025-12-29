"""Debug trace observer utilities.

This module provides a lightweight observer that can be attached to a task
observer (if supported) to record a small rolling trace of processed frames.
It also captures the most recent LLM-style message list when present.

The implementation is intentionally defensive: failures during inspection are
swallowed to avoid interfering with the main processing pipeline.
"""

from collections import deque
from collections.abc import Mapping, Sequence
from typing import Any


def _looks_like_llm_message_list(obj: Any) -> bool:
    """Return True if `obj` resembles an OpenAI-style list of messages.

    The heuristic is intentionally simple: we check that the object is a
    non-empty sequence whose first element is a mapping containing `role`
    and `content` keys.

    Args:
        obj: Arbitrary value to inspect.

    Returns:
        True if `obj` looks like a message list, otherwise False.
    """
    if not isinstance(obj, Sequence) or not obj:
        return False

    sample = obj[0]
    return isinstance(sample, Mapping) and ("role" in sample and "content" in sample)


def _full_classname(obj: Any) -> str:
    """Return the fully-qualified class name for an object.

    Args:
        obj: Object to inspect.

    Returns:
        Fully-qualified class name when available; otherwise the fallback
        `type(obj).__name__`.
    """
    try:
        return f"{obj.__class__.__module__}.{obj.__class__.__name__}"
    except Exception:
        return type(obj).__name__


class _TraceObserver:
    """Observer that records a rolling trace of frames for debugging.

    The observer stores small metadata about each frame into a deque ring
    buffer. If the frame exposes a `messages` attribute that resembles a list
    of LLM messages, it also keeps the most recent slice of messages.
    """

    def __init__(self, ring: deque[dict[str, Any]], max_msgs: int = 40) -> None:
        """Create a trace observer.

        Args:
            ring: Ring buffer to append trace entries into.
            max_msgs: Maximum number of LLM messages to keep when captured.
        """
        self._ring = ring
        self._max_msgs = max_msgs
        self._last_llm_messages: Sequence[Mapping[str, Any]] | None = None

    async def on_process_frame(self, frame: Any, *_, **__) -> None:
        """Observer hook for processed frames.

        Args:
            frame: Frame-like object.
        """
        self._record(frame)

    async def on_push_frame(self, frame: Any, *_, **__) -> None:
        """Observer hook for pushed frames.

        Args:
            frame: Frame-like object.
        """
        self._record(frame)

    def _record(self, frame: Any) -> None:
        """Record a single frame into the ring buffer.

        Args:
            frame: Frame-like object.

        Returns:
            None
        """
        try:
            cls = _full_classname(frame)
            item: dict[str, Any] = {
                "id": getattr(frame, "id", None),
                "name": getattr(frame, "name", None),
                "class": cls,
                "pts": getattr(frame, "pts", None),
            }

            # Capture the most recent LLM messages when the frame exposes them.
            if hasattr(frame, "messages"):
                messages = frame.messages
                if _looks_like_llm_message_list(messages):
                    self._last_llm_messages = messages[-self._max_msgs :]

            self._ring.append(item)
        except Exception:
            # Debug tracing must never break the main pipeline.
            pass


def attach_trace_observer(task_observer: Any, ring_size: int = 200) -> None:
    """Attach a debug trace observer to a task observer, if supported.

    This function is a no-op when `task_observer` is None, or when it does
    not provide an `add_observer` method.

    Args:
        task_observer: An object that may support `add_observer(observer)`.
        ring_size: Maximum number of trace entries to keep in the ring buffer.

    Returns:
        None
    """
    if task_observer is None:
        return

    # Initialize debug storage only once.
    if getattr(task_observer, "_debug_trace", None) is None:
        task_observer._debug_trace = deque(maxlen=ring_size)  # type: ignore[attr-defined]
        task_observer._debug_last_llm_messages = None  # type: ignore[attr-defined]

    ring: deque[dict[str, Any]] = task_observer._debug_trace  # type: ignore[attr-defined]
    observer = _TraceObserver(ring)

    try:
        add = getattr(task_observer, "add_observer", None)
        if callable(add):
            add(observer)
            # Snapshot for convenient external access.
            task_observer._debug_last_llm_messages = observer._last_llm_messages  # type: ignore[attr-defined]
    except Exception:
        # Optional debug feature; never fail hard.
        pass
