"""Connexity gateway API helpers.

This module provides small utilities used by the SDK to serialize payloads
(e.g., UUIDs) and send them to the Connexity gateway over HTTP.
"""

from typing import Any
from uuid import UUID

import aiohttp

from connexity.calls.models import CallSessionData
from connexity.constants import CONNEXITY_URL
from connexity.utils.logging_config import get_logger

logger = get_logger(__name__)


def convert_uuids(obj: Any) -> Any:
    """Recursively convert UUID objects to strings.

    This is useful before JSON-encoding payloads, since UUID is not JSON
    serializable by default.

    Args:
        obj: An arbitrary object that may contain UUID instances.

    Returns:
        The same structure as `obj`, but with UUID instances converted to
        their string representation.
    """
    if isinstance(obj, UUID):
        return str(obj)

    if isinstance(obj, dict):
        return {k: convert_uuids(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [convert_uuids(item) for item in obj]

    return obj


async def send_to_gateway(
    data: CallSessionData | dict[str, Any], api_key: str, url: str = CONNEXITY_URL
) -> None:
    """Send call-session data to Connexity's gateway API.

    Args:
        data: A `CallSessionData` model or a dict payload to send.
        api_key: API key used for the `X-API-KEY` authentication header.
        url: Gateway URL (defaults to `CONNEXITY_URL`).

    Returns:
        None
    """
    try:
        if isinstance(data, CallSessionData):
            data = data.model_dump()
        # Ensure UUID values are JSON-serializable before sending.
        converted_data = convert_uuids(data)

        # Keep requests bounded to avoid hanging call flows.
        timeout = aiohttp.ClientTimeout(total=10)

        async with (
            aiohttp.ClientSession(timeout=timeout) as session,
            session.post(
                url, headers={"X-API-KEY": api_key}, json=converted_data
            ) as response,
        ):
            if response.status != 200:
                logger.warning(f"Failed to send data (status {response.status})")
            else:
                logger.debug(f"Data sent successfully (status {response.status})")

    except TimeoutError:
        logger.warning("Timeout while sending data to API")

    except aiohttp.ClientError as e:
        logger.warning(f"Network error while sending data: {e}")

    except Exception as e:
        logger.error(f"Unexpected error while sending data: {e}", exc_info=True)
