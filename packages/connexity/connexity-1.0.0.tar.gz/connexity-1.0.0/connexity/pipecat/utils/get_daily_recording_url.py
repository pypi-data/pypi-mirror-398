"""Daily.co recording utilities for the Connexity SDK.

This module provides a small helper to fetch the most recent Daily.co cloud
recording for a given room and return a signed download URL.

All functions are best-effort: on any issue, they return `(None, None)`.
"""

from __future__ import annotations

from urllib.parse import urlparse

import requests

from connexity.utils.logging_config import get_logger

logger = get_logger(__name__)

API_BASE: str = "https://api.daily.co/v1"


def _extract_room_name(room_url: str) -> str:
    """Extract a room name from a Daily room URL.

    Daily room URLs commonly look like:
        https://<subdomain>.daily.co/<room_name>[...]

    Args:
        room_url: Full Daily room URL.

    Returns:
        The extracted room name, or an empty string if parsing fails.
    """
    path = urlparse(room_url).path.rstrip("/")
    if not path:
        return ""

    # urlparse().path includes a leading slash; split safely for nested paths.
    parts = path.strip("/").split("/")
    return parts[-1] if parts else ""


def get_daily_recording_url(
    api_key: str, room_url: str
) -> tuple[str | None, int | None]:
    """Fetch a signed URL for the most recent Daily.co cloud recording.

    Args:
        api_key: Daily REST API key (Bearer token).
        room_url: Full room URL (e.g., "https://your-domain.daily.co/test-room").

    Returns:
        A tuple of `(download_url, duration_seconds)` for the most recent
        recording, or `(None, None)` on any issue.

        Note: If a recording exists but an id is missing in the response,
        this returns `(None, duration_seconds)` to preserve existing behavior.
    """
    try:
        if not api_key:
            return None, None

        headers = {"Authorization": f"Bearer {api_key}"}

        room_name = _extract_room_name(room_url)
        if not room_name:
            return None, None

        # 1) Fetch the most recent recording for this room.
        resp = requests.get(
            f"{API_BASE}/recordings",
            headers=headers,
            params={"room_name": room_name, "limit": 1},
            timeout=15,
        )
        resp.raise_for_status()

        items = resp.json().get("data") or []
        if not items:
            return None, None

        latest = items[0]
        rec_id = latest.get("id") or latest.get("recording_id")
        duration = latest.get("duration")
        if not rec_id:
            return None, duration

        # 2) Request a signed access link.
        link_resp = requests.get(
            f"{API_BASE}/recordings/{rec_id}/access-link",
            headers=headers,
            timeout=15,
        )
        link_resp.raise_for_status()

        link_payload = link_resp.json()
        url = link_payload.get("link") or link_payload.get("download_link")
        return url, duration

    except requests.RequestException as e:
        logger.warning(f"Daily API issue: {e}")
        return None, None
    except Exception as e:
        logger.error(
            f"Unexpected issue in Daily recording fetch: {e}",
            exc_info=True,
        )
        return None, None
