"""
Utility functions for Pipecat observer operations.

This module contains static utility functions extracted from BaseConnexityObserver
for frame processing, service discovery, and provider identification.
"""

from __future__ import annotations

from typing import Any, Final

from pipecat.processors.frame_processor import FrameDirection
from pipecat.transports.base_output import BaseOutputTransport

# Optimized provider lookup using dict for O(1) token matching.
# Maps service class path substrings to canonical provider names.
# Order matters: more specific tokens should come before generic ones.
_PROVIDER_TOKEN_PRIORITY: Final[tuple[tuple[str, str], ...]] = (
    # LLM providers
    ("azure", "azure"),
    ("anthropic", "anthropic"),
    ("mistral", "mistral"),
    ("deepseek", "deepseek"),
    ("fireworks", "fireworks"),
    ("perplexity", "perplexity"),
    ("openrouter", "openrouter"),
    ("openpipe", "openpipe"),
    ("together", "together"),
    ("grok", "grok"),
    ("groq", "groq"),
    ("ollama", "ollama"),
    ("cerebras", "cerebras"),
    ("qwen", "qwen"),
    ("sambanova", "sambanova"),
    ("nim", "nvidia"),
    ("aws", "aws"),
    ("google", "google"),
    ("gemini", "google"),
    ("vertex", "google"),
    ("openai", "openai"),
    # STT providers
    ("assemblyai", "assemblyai"),
    ("deepgram", "deepgram"),
    ("speechmatics", "speechmatics"),
    ("soniox", "soniox"),
    ("gladia", "gladia"),
    ("ultravox", "ultravox"),
    ("whisper", "openai"),
    ("elevenlabs", "elevenlabs"),
    ("cartesia", "cartesia"),
    ("riva", "nvidia"),
    # TTS providers
    ("playht", "playht"),
    ("piper", "coqui"),
    ("xtts", "coqui"),
    ("hume", "hume"),
    ("lmnt", "lmnt"),
    ("neuphonic", "neuphonic"),
    ("minimax", "minimax"),
    ("rime", "rime"),
    # Other service families
    ("inworld", "inworld"),
    ("heygen", "heygen"),
    ("simli", "simli"),
    ("tavus", "tavus"),
    ("fal", "fal"),
    ("fish", "fish"),
    # Generic fallbacks (checked last due to tuple order)
    ("polly", "aws"),
    ("bedrock", "aws"),
    ("nvidia", "nvidia"),
)


def ns_to_s(ns: int) -> float:
    """
    Convert nanoseconds to seconds.

    Args:
        ns: Time value in nanoseconds.

    Returns:
        Time value in seconds as a float.
    """
    return ns / 1_000_000_000


def is_downstream_output(src: Any, direction: FrameDirection) -> bool:
    """
    Check if a frame is heading downstream to an output transport.

    Used to identify frames that are about to be sent to the user,
    which is when timing measurements should be taken.

    Args:
        src: The frame source processor.
        direction: The frame propagation direction.

    Returns:
        True if this is a downstream frame going to output transport.
    """
    return (
        isinstance(src, BaseOutputTransport)
        and direction == FrameDirection.DOWNSTREAM
    )


def apply_min_separation(
    prev_time: float | None,
    current_time: float,
    min_sep: float,
) -> float:
    """
    Ensure minimum time separation between events.

    Used to avoid registering duplicate events that occur too close
    together, which can happen with rapid frame bursts.

    Args:
        prev_time: Previous event timestamp (seconds), or None.
        current_time: Current event timestamp (seconds).
        min_sep: Minimum required separation (seconds).

    Returns:
        current_time if separation is sufficient, otherwise prev_time.
    """
    if prev_time is None or (current_time - prev_time) > min_sep:
        return current_time
    return prev_time


def trace_upstream(node: Any, max_hops: int = 20) -> list[Any]:
    """
    Trace the processor chain upstream from a given node.

    Follows the _prev attribute chain to find upstream processors.
    Used to discover LLM, STT, TTS services and context aggregators.

    Args:
        node: Starting node in the processor chain.
        max_hops: Maximum number of nodes to traverse (prevents infinite loops).

    Returns:
        List of upstream nodes in traversal order (nearest first).
    """
    chain: list[Any] = []
    seen: set[int] = set()
    cur = node

    for _ in range(max_hops):
        if cur is None or id(cur) in seen:
            break
        seen.add(id(cur))
        chain.append(cur)
        cur = getattr(cur, "_prev", None)

    return chain


def find_by_class_name(nodes: list[Any], needle: str) -> list[Any]:
    """
    Filter nodes by class name substring match.

    Args:
        nodes: List of nodes to search.
        needle: Substring to match in class names (case-sensitive).

    Returns:
        List of nodes whose class name contains the needle.
    """
    return [n for n in nodes if needle in n.__class__.__name__]


def get_switcher_active_service(switcher: Any) -> Any | None:
    """
    Extract the active service from a ServiceSwitcher.

    ServiceSwitchers allow dynamic service selection (e.g., switching
    between TTS providers). This extracts the currently active one.

    Args:
        switcher: A ServiceSwitcher instance.

    Returns:
        The currently active service, or None if not accessible.
    """
    strategy = getattr(switcher, "strategy", None)
    return getattr(strategy, "active_service", None) if strategy else None


def guess_provider(obj: Any) -> str | None:
    """
    Infer the service provider from an object's class path.

    Uses substring matching against known provider tokens to identify
    which service provider an object belongs to.

    Args:
        obj: A service object (LLM, STT, or TTS instance).

    Returns:
        Canonical provider name string, or None if unrecognized.
    """
    hay = f"{obj.__class__.__module__}.{obj.__class__.__name__}".lower()
    for token, provider in _PROVIDER_TOKEN_PRIORITY:
        if token in hay:
            return provider
    return None


def extract_model_voice(service: Any) -> tuple[str | None, str | None]:
    """
    Extract model name and voice ID from a service object.

    Attempts multiple attribute patterns used by different providers
    to find the model and voice configuration.

    Args:
        service: A Pipecat service object (LLM, STT, or TTS).

    Returns:
        Tuple of (model_name, voice_id), either may be None if not found.
    """
    # Try direct model attributes
    model = getattr(service, "model_name", None) or getattr(
        service, "_model_name", None
    )

    # Try various voice attribute patterns
    voice = (
        getattr(service, "_voice_id", None)
        or getattr(service, "voice_id", None)
        or getattr(service, "voice", None)
    )

    # Try _settings dict pattern
    settings = getattr(service, "_settings", None)
    if isinstance(settings, dict):
        model = model or settings.get("model")
        voice = voice or settings.get("voice") or settings.get("voice_id")

    # Try adapter pattern for LLM services
    get_adapter = getattr(service, "get_llm_adapter", None)
    if callable(get_adapter):
        try:
            adapter = get_adapter()
            model = (
                model
                or getattr(adapter, "model", None)
                or getattr(adapter, "model_name", None)
            )
        except Exception:
            pass

    return model, voice

