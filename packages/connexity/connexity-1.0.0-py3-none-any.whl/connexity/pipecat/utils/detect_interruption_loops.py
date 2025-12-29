"""Interruption loop detection utilities.

This module detects "interruption loops" in a sequence of overlap events.
An overlap event is represented as a dict that includes at least:
- `first_transcript_at`: float timestamp when the interrupter started speaking
- `end`: float timestamp when the overlap ended
- `interrupter_words`: int count of interrupter words detected

The public entry point is `detect_interruption_loops()`, which groups qualifying
overlaps into contiguous loop segments based on timing gaps.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class InterruptionLoopConfig:
    """Thresholds used to detect interruption loops.

    Attributes:
        min_interrupter_words: Minimum interrupter word count for an overlap to
            qualify.
        min_overlap_duration: Minimum duration (seconds) of an overlap to
            qualify.
        min_overlaps_in_loop: Minimum number of qualifying overlaps required to
            form a loop.
        max_gap_between_overlaps: Maximum allowed gap (seconds) between
            consecutive overlaps for them to be considered part of the same loop.
    """

    min_interrupter_words: int = 2
    min_overlap_duration: float = 0.5
    min_overlaps_in_loop: int = 2
    max_gap_between_overlaps: float = 10.0


DEFAULT_INTERRUPTION_LOOP_CONFIG = InterruptionLoopConfig()


def _overlap_duration(overlap: dict[str, Any]) -> float | None:
    """Compute overlap duration from a single overlap dict.

    Args:
        overlap: Overlap event dict.

    Returns:
        Duration in seconds, or None if required timestamps are missing.
    """

    first_ts = overlap.get("first_transcript_at")
    end_ts = overlap.get("end")
    if first_ts is None or end_ts is None:
        return None
    return max(0.0, end_ts - first_ts)


def _qualifies(overlap: dict[str, Any], config: InterruptionLoopConfig) -> bool:
    """Check whether a single overlap qualifies for loop detection."""

    duration = _overlap_duration(overlap)
    if duration is None:
        return False
    if duration < config.min_overlap_duration:
        return False

    interrupter_words = overlap.get("interrupter_words", 0)
    return interrupter_words >= config.min_interrupter_words


def detect_interruption_loops(
    overlaps: Sequence[dict[str, Any]] | None,
    *,
    config: InterruptionLoopConfig = DEFAULT_INTERRUPTION_LOOP_CONFIG,
) -> list[dict[str, Any]]:
    """Detect interruption loops from a sequence of overlaps.

    Args:
        overlaps: Iterable of overlap dictionaries. Each overlap should contain at
            least the keys: ``first_transcript_at`` (float), ``end`` (float),
            ``interrupter_words`` (int).
        config: Configuration thresholds for detection.

    Returns:
        List of dicts, each representing an interruption loop with keys:
            ``loop_start``: first transcript time of first overlap in loop
            ``loop_end``: end time of last overlap in loop
            ``overlaps``: list of overlap dicts in the loop (shallow copies)
            ``thresholds``: copy of thresholds used to detect the loop
    """

    if not overlaps:
        return []

    qualifying = [overlap for overlap in overlaps if _qualifies(overlap, config)]
    if len(qualifying) < config.min_overlaps_in_loop:
        return []

    # Ensure chronological evaluation regardless of input ordering.
    qualifying.sort(key=lambda o: o.get("first_transcript_at", float("inf")))

    loops: list[dict[str, Any]] = []
    loop_candidate_overlaps: list[dict[str, Any]] = []

    for overlap in qualifying:
        first_ts = overlap.get("first_transcript_at")
        end_ts = overlap.get("end")
        if first_ts is None or end_ts is None:
            # Skip malformed overlaps (consistent with prior behavior).
            continue

        if not loop_candidate_overlaps:
            loop_candidate_overlaps.append(overlap)
            continue

        prev_end = loop_candidate_overlaps[-1].get("end")
        gap = (first_ts - prev_end) if (prev_end is not None) else None

        # If the gap is small enough, keep accumulating in the same loop.
        if gap is not None and gap < config.max_gap_between_overlaps:
            loop_candidate_overlaps.append(overlap)
            continue

        # Gap too large (or unknown): close out any valid loop candidate.
        if len(loop_candidate_overlaps) >= config.min_overlaps_in_loop:
            loops.append(_record_loop(overlaps=loop_candidate_overlaps, config=config))
        loop_candidate_overlaps = [overlap]

    # Final candidate at end of iteration.
    if len(loop_candidate_overlaps) >= config.min_overlaps_in_loop:
        loops.append(_record_loop(overlaps=loop_candidate_overlaps, config=config))

    return loops


def _record_loop(
    overlaps: Sequence[dict[str, Any]],
    config: InterruptionLoopConfig,
) -> dict[str, Any]:
    """Build the output payload for a detected loop."""

    start_ts = overlaps[0].get("first_transcript_at")
    end_ts = overlaps[-1].get("end")

    # Shallow-copy overlap dicts to avoid callers mutating original inputs.
    overlaps_copy = [dict(overlap) for overlap in overlaps]

    return {
        "loop_start": start_ts,
        "loop_end": end_ts,
        "overlaps": overlaps_copy,
        "thresholds": {
            "min_interrupter_words": config.min_interrupter_words,
            "min_overlap_duration_secs": config.min_overlap_duration,
            "min_overlaps_in_loop": config.min_overlaps_in_loop,
            "max_gap_between_overlaps_secs": config.max_gap_between_overlaps,
        },
    }
