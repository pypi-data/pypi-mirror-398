"""
Snapshot utilities for capturing and serializing error frames in Pipecat pipelines.

This module provides comprehensive error frame snapshotting capabilities for debugging
and diagnostics in Pipecat-based voice/AI pipelines. It captures processor state,
async primitives, LLM messages, and related metadata while ensuring sensitive data
(API keys, tokens, etc.) is properly redacted.

Key Features:
    - Sensitive data redaction (API keys, tokens, secrets)
    - JSON-safe conversion of complex Python objects
    - Asyncio primitive introspection (queues, events, tasks)
    - Processor state capture with categorized attributes
    - LLM message extraction from nested structures
"""

from __future__ import annotations

import asyncio
import contextlib
import inspect
import re
import sys
import time
from collections import deque
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, is_dataclass
from importlib import metadata as importlib_metadata
from typing import Any, Final, Literal

from connexity.calls.messages.issue_message import IssueMessage
from connexity.utils.logging_config import get_logger

logger = get_logger(__name__)

# Category label for network-related attributes
NETWORK_LABEL: Final[str] = "network"

# Maximum recursion depth for JSON conversion
_DEFAULT_MAX_DEPTH: Final[int] = 3

# Maximum items to process in collections to prevent memory issues
_MAX_MAPPING_ITEMS: Final[int] = 1000
_MAX_SEQUENCE_ITEMS: Final[int] = 200
_MAX_SCALAR_ITEMS: Final[int] = 20


# =============================================================================
# Sensitive Data Redaction Configuration
# =============================================================================

# Keys that require exact match for redaction (case-insensitive)
REDACT_KEYS_EXACT: Final[frozenset[str]] = frozenset(
    {
        "api_key",
        "apikey",
        "token",
        "access_token",
        "refresh_token",
        "id_token",
        "auth",
        "authorization",
        "secret",
        "password",
        "bearer",
    }
)

# Keys containing "token" that should NOT be redacted (e.g., model config)
REDACT_SAFE_TOK_KEYS: Final[frozenset[str]] = frozenset(
    {
        "max_tokens",
        "max_completion_tokens",
    }
)

# Key suffixes that trigger redaction
REDACT_KEY_SUFFIXES: Final[tuple[str, ...]] = (
    "_key",
    "_api_key",
    "_apikey",
    "_token",
    "_tokens",
    "_secret",
    "_password",
    "_auth",
    "_authorization",
)

# Pre-compiled patterns for detecting sensitive values in strings
REDACT_VALUE_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"\bsk_[A-Za-z0-9]{16,}\b"),  # OpenAI-style API keys
    re.compile(
        r"\bbearer\s+[A-Za-z0-9\-\._~\+\/]+=*\b", re.IGNORECASE
    ),  # Bearer tokens
    re.compile(
        r"eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}"
    ),  # JWTs
)

_REDACTED_PLACEHOLDER: Final[str] = "***REDACTED***"


# =============================================================================
# Version Detection
# =============================================================================


def _pipecat_version() -> str | None:
    """
    Retrieve the installed Pipecat library version.

    Attempts to find the version through multiple methods:
    1. Check importlib metadata for 'pipecat-ai' or 'pipecat' packages
    2. Fall back to checking the __version__ attribute on the module

    Returns:
        The version string if found, None otherwise.
    """
    for dist in ("pipecat-ai", "pipecat"):
        try:
            return importlib_metadata.version(dist)
        except importlib_metadata.PackageNotFoundError:
            continue

    try:
        import pipecat  # type: ignore[import-not-found]

        return getattr(pipecat, "__version__", None)
    except Exception:
        return None


# =============================================================================
# Redaction Utilities
# =============================================================================


def _should_redact_key(key: str) -> bool:
    """
    Determine if a dictionary key should have its value redacted.

    Uses a multi-tier check: safe-list exclusion, exact match, then suffix match.

    Args:
        key: The dictionary key to evaluate.

    Returns:
        True if the associated value should be redacted, False otherwise.
    """
    lower_key = (key or "").lower()

    # Explicitly safe keys should never be redacted
    if lower_key in REDACT_SAFE_TOK_KEYS:
        return False

    # Exact match against known sensitive key names
    if lower_key in REDACT_KEYS_EXACT:
        return True

    # Suffix-based detection for keys like 'openai_api_key'
    return any(lower_key.endswith(suffix) for suffix in REDACT_KEY_SUFFIXES)


def _should_redact_value(val: Any) -> bool:
    """
    Determine if a string value contains sensitive data patterns.

    Checks for common credential patterns like API keys, bearer tokens, and JWTs.

    Args:
        val: The value to evaluate.

    Returns:
        True if the value matches a sensitive data pattern, False otherwise.
    """
    if not isinstance(val, str):
        return False
    return any(pattern.search(val) for pattern in REDACT_VALUE_PATTERNS)


# =============================================================================
# String Representation Utilities
# =============================================================================


def _short_repr(obj: Any, max_len: int = 200) -> str:
    """
    Generate a truncated string representation of an object.

    Attempts repr() first, falls back to str(), and finally creates a
    minimal representation if both fail.

    Args:
        obj: The object to represent.
        max_len: Maximum length of the returned string.

    Returns:
        A string representation, truncated with '…' if exceeding max_len.
    """
    try:
        result = repr(obj)
    except Exception:
        try:
            result = str(obj)
        except Exception:
            result = f"<unreprable {type(obj).__name__} at 0x{id(obj):x}>"

    if len(result) <= max_len:
        return result
    return result[: max_len - 1] + "…"


def _full_classname(obj: Any) -> str:
    """
    Get the fully qualified class name of an object.

    Args:
        obj: The object to get the class name for.

    Returns:
        Fully qualified name (module.classname) or just the type name on failure.
    """
    try:
        return f"{obj.__class__.__module__}.{obj.__class__.__name__}"
    except Exception:
        return type(obj).__name__


# =============================================================================
# JSON-Safe Conversion
# =============================================================================


def _to_jsonable(
    value: Any,
    depth: int = 0,
    max_depth: int = _DEFAULT_MAX_DEPTH,
) -> Any:
    """
    Recursively convert a Python object to a JSON-serializable representation.

    Handles primitives, dataclasses, mappings, sequences, and binary data.
    Automatically redacts sensitive values and keys.

    Args:
        value: The value to convert.
        depth: Current recursion depth (internal use).
        max_depth: Maximum recursion depth before falling back to repr().

    Returns:
        A JSON-serializable representation of the value.
    """
    # Primitives pass through directly (with optional redaction)
    if value is None or isinstance(value, (bool, int, float)):
        return value

    if isinstance(value, str):
        return _REDACTED_PLACEHOLDER if _should_redact_value(value) else value

    # Prevent infinite recursion on deeply nested structures
    if depth >= max_depth:
        return _short_repr(value)

    # Dataclasses: convert to dict first
    if is_dataclass(value) and not isinstance(value, type):
        try:
            return _to_jsonable(asdict(value), depth + 1, max_depth)
        except Exception:
            return _short_repr(value)

    # Mappings: process key-value pairs with redaction
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        items = list(value.items())[:_MAX_MAPPING_ITEMS]
        for key, val in items:
            str_key = str(key)
            if _should_redact_key(str_key):
                result[str_key] = _REDACTED_PLACEHOLDER
            else:
                result[str_key] = _to_jsonable(val, depth + 1, max_depth)
        return result

    # Sequences: convert elements recursively
    if isinstance(value, (list, tuple, set)):
        sequence: Iterable[Any] = list(value)[:_MAX_SEQUENCE_ITEMS]
        return [_to_jsonable(item, depth + 1, max_depth) for item in sequence]

    # Binary data: return type and length only
    if isinstance(value, (bytes, bytearray)):
        return {"type": type(value).__name__, "len": len(value)}

    return _short_repr(value)


# =============================================================================
# Asyncio Type Probes
# =============================================================================


def _is_queue(obj: Any) -> bool:
    """
    Check if an object is an asyncio or standard library queue.

    Args:
        obj: The object to check.

    Returns:
        True if the object is a queue instance.
    """
    try:
        import queue as std_queue

        return isinstance(obj, (asyncio.Queue, std_queue.Queue))
    except Exception:
        return isinstance(obj, asyncio.Queue)


def _is_event(obj: Any) -> bool:
    """
    Check if an object is an asyncio Event.

    Args:
        obj: The object to check.

    Returns:
        True if the object is an asyncio.Event instance.
    """
    return isinstance(obj, asyncio.Event)


def _is_task(obj: Any) -> bool:
    """
    Check if an object is an asyncio Task.

    Args:
        obj: The object to check.

    Returns:
        True if the object is an asyncio.Task instance.
    """
    return isinstance(obj, asyncio.Task)


# =============================================================================
# Asyncio Object Snapshots
# =============================================================================


def _queue_snapshot(queue: Any) -> dict[str, Any]:
    """
    Capture the state of a queue object.

    Args:
        queue: The queue to snapshot (asyncio.Queue or queue.Queue).

    Returns:
        Dictionary containing queue type, size, repr, and a peek at contents.
    """
    snapshot: dict[str, Any] = {"type": type(queue).__name__}

    with contextlib.suppress(Exception):
        snapshot["qsize"] = queue.qsize()

    snapshot["repr"] = _short_repr(queue)

    # Attempt to peek at queue contents via internal buffer
    for attr in ("_queue", "queue"):
        if hasattr(queue, attr):
            try:
                buffer = list(getattr(queue, attr))
                snapshot["peek"] = _to_jsonable(buffer[:3], max_depth=1)
                break
            except Exception:
                pass

    return snapshot


def _event_snapshot(event: asyncio.Event) -> dict[str, Any]:
    """
    Capture the state of an asyncio Event.

    Args:
        event: The asyncio.Event to snapshot.

    Returns:
        Dictionary containing event type and current set state.
    """
    return {"type": type(event).__name__, "is_set": event.is_set()}


def _task_stack_summary(task: asyncio.Task, limit: int = 1) -> dict[str, Any] | None:
    """
    Extract a summary of the top stack frame from an asyncio Task.

    Args:
        task: The asyncio.Task to inspect.
        limit: Maximum number of stack frames to retrieve.

    Returns:
        Dictionary with file, line, and function info, or None if unavailable.
    """
    frames = task.get_stack(limit)
    if not frames:
        return None

    frame = frames[-1]
    info = inspect.getframeinfo(frame)
    return {"file": info.filename, "line": info.lineno, "func": info.function}


def _task_snapshot(task: asyncio.Task, with_stack: bool) -> dict[str, Any]:
    """
    Capture comprehensive state of an asyncio Task.

    Args:
        task: The asyncio.Task to snapshot.
        with_stack: Whether to include stack trace information.

    Returns:
        Dictionary containing task name, status, and optional stack/exception info.
    """
    data: dict[str, Any] = {
        "type": type(task).__name__,
        "name": task.get_name() if hasattr(task, "get_name") else None,
        "done": task.done(),
        "cancelled": task.cancelled(),
    }

    # Capture stack trace for running tasks
    if with_stack and not task.done():
        with contextlib.suppress(Exception):
            data["top_stack"] = _task_stack_summary(task)

    # Capture exception info for completed (non-cancelled) tasks
    if task.done() and not task.cancelled():
        try:
            exc = task.exception()
            if exc is not None:
                data["exception_type"] = type(exc).__name__
                data["exception"] = _short_repr(exc, 400)
        except Exception as err:
            data["exception_probe_error"] = str(err)

    return data


# =============================================================================
# LLM Message Extraction
# =============================================================================


def _looks_like_llm_message_list(obj: Any) -> bool:
    """
    Heuristically determine if an object looks like an LLM message list.

    Checks if the object is a non-empty sequence where the first element
    is a mapping containing 'role' and 'content' keys.

    Args:
        obj: The object to evaluate.

    Returns:
        True if the object appears to be an LLM message list.
    """
    if not isinstance(obj, Sequence) or not obj:
        return False
    sample = obj[0]
    return isinstance(sample, Mapping) and "role" in sample and "content" in sample


def extract_llm_messages_from_mappings(
    mapping: Mapping,
    max_depth: int = 2,
) -> Sequence[Mapping] | None:
    """
    Recursively search for LLM message lists within a nested mapping structure.

    Looks for keys named 'messages' (case-insensitive) whose values appear
    to be LLM message lists.

    Args:
        mapping: The mapping to search.
        max_depth: Maximum recursion depth for nested mappings.

    Returns:
        The LLM message list if found, None otherwise.
    """
    try:
        for key, value in mapping.items():
            if str(key).lower() == "messages" and _looks_like_llm_message_list(value):
                return value
            if max_depth > 0 and isinstance(value, Mapping):
                inner = extract_llm_messages_from_mappings(value, max_depth - 1)
                if inner:
                    return inner
    except Exception:
        pass
    return None


# =============================================================================
# Attribute Categorization
# =============================================================================

# Token patterns for categorization (moved outside function for performance)
_MODEL_AUDIO_TOKENS: Final[frozenset[str]] = frozenset(
    {
        "voice",
        "sample_rate",
        "samplerate",
        "channels",
        "codec",
        "format",
        "output_format",
        "bitrate",
        "audio",
    }
)

_TIMING_TOKENS: Final[frozenset[str]] = frozenset(
    {
        "retry",
        "timeout",
        "time",
        "timestamp",
        "ttfb",
        "latency",
        "duration",
        "cumulative",
    }
)

_NETWORK_TOKENS: Final[frozenset[str]] = frozenset(
    {
        "url",
        "websocket",
        "client",
        "adapter",
        "endpoint",
        "host",
        "port",
        "headers",
        "api_key",
        "apikey",
        "token",
        "auth",
        "reconnect",
    }
)


def _contains_token(name: str, tokens: frozenset[str]) -> bool:
    """
    Check if a name contains any of the specified token substrings.

    Special handling for 'ws' token to avoid false positives.

    Args:
        name: The normalized (lowercase) attribute name.
        tokens: Set of token substrings to check for.

    Returns:
        True if any token is found in the name.
    """
    for token in tokens:
        if token == "ws":
            # Special handling for 'ws' to minimize false positives
            if (
                name == "ws"
                or name.startswith("ws_")
                or name.endswith("_ws")
                or "_ws_" in name
                or name.startswith("ws")
                or name.endswith("ws")
            ):
                return True
        elif token in name:
            return True
    return False


def _categorize_attr(name: str, value: Any) -> str:
    """
    Classify a processor attribute into a semantic category.

    Categories are used to organize processor state snapshots into logical
    groups for easier debugging and analysis.

    Args:
        name: The attribute name.
        value: The attribute value (used for type-based categorization).

    Returns:
        A category label string (e.g., 'config', 'runtime', 'network').
    """
    normalized = (name or "").lower()

    # Exact-name overrides (highest priority)
    if normalized in {"_settings", "_session_properties"}:
        return "config"
    if normalized in {"_task_manager", "_clock", "_observer"}:
        return "runtime"

    # Voice-related takes precedence
    if "voice" in normalized:
        return "model_audio"

    # Context/session identifiers
    if normalized in {"context_id", "_context_id", "session_id", "_session_id"}:
        return "contexts"

    # Identity fields
    if normalized in {"_id", "id", "_name", "name"} or normalized.endswith("_id"):
        return "identity"

    # Event handlers
    if "event_handler" in normalized or normalized.startswith("on_"):
        return "event_handlers"

    # Asyncio primitives
    if "queue" in normalized:
        return "asyncio_queues"
    if normalized.endswith("_tasks") or (
        "task" in normalized and not isinstance(value, asyncio.Task)
    ):
        return "asyncio_tasks"
    if "event" in normalized:
        return "asyncio_events"

    # Model/Audio configuration
    if _contains_token(normalized, _MODEL_AUDIO_TOKENS):
        return "model_audio"
    if "model" in normalized:
        return "model"

    # Metrics
    if "metrics" in normalized:
        return "metrics"

    # Timing-related
    if _contains_token(normalized, _TIMING_TOKENS):
        return "timing"

    # Network-related
    if _contains_token(normalized, _NETWORK_TOKENS):
        return NETWORK_LABEL

    # Contexts (generic)
    if "context" in normalized or "session" in normalized:
        return "contexts"

    return "flags_other"


# =============================================================================
# Component Snapshot Helpers
# =============================================================================


def _scalar_state_from_dictish(
    obj: Any, max_items: int = _MAX_SCALAR_ITEMS
) -> dict[str, Any]:
    """
    Extract scalar (primitive) values from an object's __dict__.

    Useful for capturing simple state without including complex nested objects.

    Args:
        obj: The object to extract scalar state from.
        max_items: Maximum number of items to extract.

    Returns:
        Dictionary of scalar attribute names to values.
    """
    result: dict[str, Any] = {}
    obj_dict = getattr(obj, "__dict__", None)

    if not isinstance(obj_dict, dict):
        return result

    for idx, (key, val) in enumerate(obj_dict.items()):
        if idx >= max_items:
            break
        if isinstance(val, (bool, int, float, str, type(None))):
            result[key] = val

    return result


def _snapshot_clock(clock: Any) -> dict[str, Any]:
    """
    Capture the state of a clock/timer object.

    Args:
        clock: The clock object to snapshot.

    Returns:
        Dictionary containing class name and scalar state.
    """
    data: dict[str, Any] = {"class": _full_classname(clock)}
    data.update(_scalar_state_from_dictish(clock))
    return data


def _snapshot_task_manager(task_manager: Any) -> dict[str, Any]:
    """
    Capture the state of a task manager object.

    Args:
        task_manager: The task manager to snapshot.

    Returns:
        Dictionary containing class name, pending task count, and scalar state.
    """
    data: dict[str, Any] = {"class": _full_classname(task_manager)}

    try:
        tasks = getattr(task_manager, "_tasks", None)
        if isinstance(tasks, (set, list, tuple)):
            data["pending_tasks"] = len(tasks)
    except Exception:
        pass

    data.update(_scalar_state_from_dictish(task_manager))
    return data


def _snapshot_task_observer(observer: Any) -> dict[str, Any]:
    """
    Capture the state of a task observer object.

    Args:
        observer: The task observer to snapshot.

    Returns:
        Dictionary containing class name, trace length, and scalar state.
    """
    data: dict[str, Any] = {"class": _full_classname(observer)}

    try:
        ring = getattr(observer, "_debug_trace", None)
        if isinstance(ring, deque):
            data["trace_len"] = len(ring)
    except Exception:
        pass

    data.update(_scalar_state_from_dictish(observer))
    return data


def _snapshot_strategy(strategy: Any) -> dict[str, Any]:
    """
    Capture the state of an interruption strategy object.

    Args:
        strategy: The strategy object to snapshot.

    Returns:
        Dictionary containing class name and scalar state.
    """
    data: dict[str, Any] = {"class": _full_classname(strategy)}
    data.update(_scalar_state_from_dictish(strategy))
    return data


def _schema_to_json(schema: Any) -> Any:
    """
    Convert a schema object to a JSON-serializable format.

    Handles Pydantic models (v1 and v2) and falls back to generic conversion.

    Args:
        schema: The schema object to convert.

    Returns:
        JSON-serializable representation of the schema.
    """
    if schema is None:
        return None

    try:
        # Pydantic v2 style
        dump = getattr(schema, "model_dump", None)
        if callable(dump):
            return _to_jsonable(dump())

        # Pydantic v1 style
        dump = getattr(schema, "dict", None)
        if callable(dump):
            return _to_jsonable(dump())

        return _to_jsonable(schema)
    except Exception:
        return _short_repr(schema)


def _extract_schema_from_entry(entry: Any) -> Any:
    """
    Extract a function schema from a handler registry entry.

    Attempts to instantiate the handler's parent class to retrieve
    the schema definition.

    Args:
        entry: The registry entry containing a handler.

    Returns:
        The schema dictionary if found, None otherwise.
    """
    handler = entry.handler
    if not handler:
        return None

    try:
        handler_class_entity = handler.__self__.__class__(metadata={})
        schema = getattr(handler_class_entity, "schema", None)
        return schema.__dict__ if schema else None
    except Exception as err:
        logger.debug("Error extracting handler schema: %s", err)
        return None


# =============================================================================
# Frame and Processor Snapshots
# =============================================================================


def snapshot_frame_common(frame: Any) -> dict[str, Any]:
    """
    Capture common fields from a frame object.

    Args:
        frame: The frame object to snapshot.

    Returns:
        Dictionary containing standard frame fields (id, name, pts, metadata, etc.).
    """
    fields = (
        "id",
        "name",
        "pts",
        "metadata",
        "transport_source",
        "transport_destination",
    )
    return {field: _to_jsonable(getattr(frame, field, None)) for field in fields}


def _snapshot_event_handlers(event_handlers: Any) -> dict[str, Any]:
    """
    Capture the state of event handler registrations.

    Args:
        event_handlers: The event handlers mapping to snapshot.

    Returns:
        Dictionary containing handler information keyed by event name.
    """
    result: dict[str, Any] = {}

    if isinstance(event_handlers, Mapping):
        for name, handler in event_handlers.items():
            info: dict[str, Any] = {"repr": _short_repr(handler)}

            try:
                handlers = getattr(handler, "handlers", None)
                if handlers is not None:
                    info["handlers_count"] = (
                        len(list(handlers))
                        if isinstance(handlers, (list, tuple, set))
                        else None
                    )
            except Exception:
                pass

            info["is_sync"] = getattr(handler, "is_sync", None)
            result[str(name)] = info
    else:
        result["repr"] = _short_repr(event_handlers)

    return result


def _snapshot_metrics(metrics: Any) -> dict[str, Any]:
    """
    Capture the state of a metrics tracking object.

    Args:
        metrics: The metrics object to snapshot.

    Returns:
        Dictionary containing TTFB, timing info, and processing state.
    """
    if metrics is None:
        return {}

    data: dict[str, Any] = {"class": _full_classname(metrics)}

    with contextlib.suppress(Exception):
        data["ttfb"] = getattr(metrics, "ttfb", None)

    # Capture internal timing attributes
    for attr in ("_start_ttfb_time", "_last_ttfb_time", "_start_processing_time"):
        if hasattr(metrics, attr):
            data[attr] = getattr(metrics, attr)

    # Calculate processing state
    try:
        start_time = getattr(metrics, "_start_processing_time", 0) or 0
        if start_time > 0:
            data["processing_in_progress"] = True
            data["processing_elapsed"] = time.time() - start_time
        else:
            data["processing_in_progress"] = False
    except Exception:
        pass

    # Core metrics data
    core_data = getattr(metrics, "_core_metrics_data", None)
    if core_data is not None:
        data["core"] = {
            "processor": getattr(core_data, "processor", None),
            "model": getattr(core_data, "model", None),
        }

    # Associated task manager
    task_mgr = getattr(metrics, "_task_manager", None)
    if task_mgr is not None:
        data["task_manager"] = {"class": _full_classname(task_mgr)}

    return data


def snapshot_processor(
    proc: Any,
    *,
    include_task_stacks: bool = True,
) -> dict[str, Any]:
    """
    Capture comprehensive state of a Pipecat processor.

    Performs a deep inspection of the processor, capturing configuration,
    runtime state, asyncio primitives, LLM messages, and related metadata.
    Attributes are categorized into logical groups for easier analysis.

    Args:
        proc: The processor object to snapshot.
        include_task_stacks: Whether to include stack traces for running tasks.

    Returns:
        Dictionary containing categorized processor state, or empty dict if proc is None.
    """
    if proc is None:
        return {}

    snapshot: dict[str, Any] = {"class": _full_classname(proc)}

    # Capture identity fields
    for attr in ("_name", "_id"):
        if hasattr(proc, attr):
            key = "name" if attr == "_name" else "id"
            snapshot[key] = _to_jsonable(getattr(proc, attr))

    # Capture prev/next pipeline links
    for side in ("_prev", "_next"):
        linked_obj = getattr(proc, side, None)
        if linked_obj is not None:
            snapshot[side] = {
                "class": _full_classname(linked_obj),
                "name": _short_repr(getattr(linked_obj, "_name", None)),
                "id": getattr(linked_obj, "_id", None),
                "repr": _short_repr(linked_obj),
            }

    # Capture structured known fields
    if hasattr(proc, "_settings"):
        snapshot["_settings"] = _to_jsonable(proc._settings, max_depth=3)

    if hasattr(proc, "_session_properties"):
        snapshot["_session_properties"] = _to_jsonable(
            proc._session_properties, max_depth=3
        )

    if hasattr(proc, "_event_handlers"):
        snapshot["_event_handlers"] = _snapshot_event_handlers(proc._event_handlers)

    # Capture metrics
    if hasattr(proc, "_metrics"):
        snapshot["metrics"] = _snapshot_metrics(proc._metrics)

    # Capture contexts
    if hasattr(proc, "_contexts"):
        ctx = proc._contexts
        if isinstance(ctx, Mapping):
            details = {}
            for key, val in ctx.items():
                details[str(key)] = (
                    _queue_snapshot(val) if _is_queue(val) else _short_repr(val)
                )
            snapshot["_contexts"] = {"count": len(ctx), "items": details}
        else:
            snapshot["_contexts"] = _short_repr(ctx)

    # Attributes already handled (skip during dynamic scan)
    skip_attrs: frozenset[str] = frozenset(
        {
            "_name",
            "_id",
            "_settings",
            "_session_properties",
            "_event_handlers",
            "_prev",
            "_next",
            "_metrics",
            "_contexts",
        }
    )

    buckets: dict[str, dict[str, Any]] = {}

    # Dynamic scan of remaining attributes
    for attr_name, attr_val in getattr(proc, "__dict__", {}).items():
        if attr_name in skip_attrs:
            continue

        # Handle specific opaque objects with dedicated snapshot functions
        if attr_name == "_clock":
            buckets.setdefault("runtime", {})[attr_name] = _snapshot_clock(attr_val)
            continue

        if attr_name == "_task_manager":
            buckets.setdefault("runtime", {})[attr_name] = _snapshot_task_manager(
                attr_val
            )
            continue

        if attr_name == "_observer":
            buckets.setdefault("runtime", {})[attr_name] = _snapshot_task_observer(
                attr_val
            )
            continue

        if attr_name == "_interruption_strategies":
            items = []
            try:
                strategies = (
                    list(attr_val) if isinstance(attr_val, (list, tuple, set)) else []
                )
                items = [_snapshot_strategy(s) for s in strategies]
            except Exception:
                pass
            buckets.setdefault("flags_other", {})[attr_name] = items
            continue

        if attr_name == "_functions":
            expanded = _expand_functions_registry(attr_val)
            buckets.setdefault("flags_other", {})[attr_name] = expanded
            continue

        # Type-based bucket assignment for asyncio primitives
        try:
            if _is_queue(attr_val):
                buckets.setdefault("asyncio_queues", {})[attr_name] = _queue_snapshot(
                    attr_val
                )
                continue

            if _is_event(attr_val):
                buckets.setdefault("asyncio_events", {})[attr_name] = _event_snapshot(
                    attr_val
                )
                continue

            if _is_task(attr_val):
                buckets.setdefault("asyncio_tasks", {})[attr_name] = _task_snapshot(
                    attr_val, include_task_stacks
                )
                continue

            # Collection of tasks
            if (
                isinstance(attr_val, (set, list, tuple))
                and attr_val
                and all(isinstance(x, asyncio.Task) for x in attr_val)
            ):
                buckets.setdefault("asyncio_tasks", {})[attr_name] = [
                    _task_snapshot(x, include_task_stacks) for x in attr_val
                ]
                continue
        except Exception:
            pass

        # Generic categorization for remaining attributes
        category = _categorize_attr(attr_name, attr_val)
        if attr_name == "_task_manager" and category == "asyncio_tasks":
            category = "runtime"
        buckets.setdefault(category, {})[attr_name] = _to_jsonable(attr_val)

    # Promote buckets to snapshot in defined order
    promotion_order = (
        "runtime",
        "flags_other",
        "model_audio",
        NETWORK_LABEL,
        "network_llm",
        "timing",
        "metrics",
        "contexts",
        "config",
        "asyncio_queues",
        "asyncio_events",
        "asyncio_tasks",
    )

    for category in promotion_order:
        if category in buckets and buckets[category]:
            if category == "metrics":
                snapshot.setdefault("metrics", {}).update(buckets[category])
            else:
                snapshot[category] = buckets[category]

    # Add remaining categories not in promotion order
    for category, payload in buckets.items():
        if category not in promotion_order and payload:
            snapshot[category] = payload

    # Capture adapter/client summary
    for key in ("_adapter", "_client"):
        if hasattr(proc, key):
            val = getattr(proc, key)
            snapshot[key] = {"class": _full_classname(val), "repr": _short_repr(val)}

    # Extract LLM messages heuristically
    try:
        llm_messages = extract_llm_messages_from_mappings(getattr(proc, "__dict__", {}))
        if llm_messages:
            snapshot["llm_messages"] = _to_jsonable(llm_messages, max_depth=3)
    except Exception:
        pass

    # Capture observer debug trace
    obs = getattr(proc, "_observer", None)
    if obs is not None:
        ring = getattr(obs, "_debug_trace", None)
        if isinstance(ring, deque):
            snapshot["trace"] = list(ring)[-20:]

        last_msgs = getattr(obs, "_debug_last_llm_messages", None)
        if last_msgs:
            snapshot.setdefault("llm_messages", _to_jsonable(last_msgs, max_depth=3))

    return snapshot


def _expand_functions_registry(registry: Any) -> dict[str, Any]:
    """
    Expand a functions registry into a JSON-serializable format.

    Handles both mapping-based and object-based registry entries,
    extracting function names, handlers, and schemas.

    Args:
        registry: The functions registry to expand.

    Returns:
        Dictionary of function names to their metadata.
    """
    expanded: dict[str, Any] = {}

    try:
        if not isinstance(registry, Mapping):
            return {"repr": _short_repr(registry)}

        for func_name, raw in registry.items():
            record: dict[str, Any] = {}

            if isinstance(raw, Mapping):
                record["function_name"] = str(raw.get("function_name", func_name))
                record["cancel_on_interruption"] = raw.get("cancel_on_interruption")
                record["handler_deprecated"] = raw.get("handler_deprecated")
                record["handler"] = _short_repr(raw.get("handler", raw))
                schema_obj = _extract_schema_from_entry(raw)
            else:
                record["function_name"] = getattr(raw, "function_name", func_name)
                record["cancel_on_interruption"] = getattr(
                    raw, "cancel_on_interruption", None
                )
                record["handler_deprecated"] = getattr(raw, "handler_deprecated", None)
                handler_obj = getattr(raw, "handler", raw)
                record["handler"] = _short_repr(handler_obj)
                schema_obj = _extract_schema_from_entry(raw)

            record["schema"] = _schema_to_json(schema_obj)
            expanded[str(func_name)] = record

    except Exception:
        expanded["repr"] = _short_repr(registry)

    return expanded


# =============================================================================
# Error Source Detection
# =============================================================================

# Mapping of processor name patterns to error source types
_ERROR_SOURCE_PATTERNS: Final[dict[str, str]] = {
    "Transport": "transport",
    "Filter": "frame_filter",
    "Observer": "observer",
    "FrameProcessor": "frame_processor",
    "FrameSerializer": "frame_serializer",
    "Switcher": "switcher",
    "LLMService": "llm_service",
    "TTSService": "tts_service",
    "STTService": "stt_service",
    "ToolCall": "tool_call",
}

ErrorSourceType = Literal[
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


def _get_error_source(processor: Any) -> ErrorSourceType:
    """
    Heuristically determine the component type that generated an error.

    Inspects the processor name for known patterns to classify the
    error source for diagnostic purposes.

    Args:
        processor: The processor that generated the error.

    Returns:
        A string literal indicating the error source type.
    """
    processor_name = getattr(processor, "name", "")

    for pattern, source_type in _ERROR_SOURCE_PATTERNS.items():
        if pattern in processor_name:
            return source_type  # type: ignore[return-value]

    return "unknown"


# =============================================================================
# Main Entry Point
# =============================================================================


def snapshot_error_frame(
    err_frame: Any,
    seconds_from_start: float,
    *,
    include_task_stacks: bool = True,
) -> IssueMessage:
    """
    Create a comprehensive snapshot of an error frame for diagnostics.

    Captures the error frame state, processor state, and environment metadata
    into an IssueMessage suitable for logging, reporting, or analysis.

    Args:
        err_frame: The error frame object containing the issue and processor.
        seconds_from_start: Elapsed time in seconds since pipeline start.
        include_task_stacks: Whether to include stack traces for running tasks.

    Returns:
        An IssueMessage containing the error content, source classification,
        timing, and comprehensive metadata about the error context.
    """
    return IssueMessage(
        content=getattr(err_frame, "issue", None),
        source=_get_error_source(err_frame.processor),
        seconds_from_start=seconds_from_start,
        metadata={
            "error_frame": snapshot_frame_common(err_frame),
            "processor": snapshot_processor(
                getattr(err_frame, "processor", None),
                include_task_stacks=include_task_stacks,
            ),
            "pipecat_version": _pipecat_version(),
            "python": sys.version.split()[0],
        },
    )
