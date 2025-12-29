"""Twilio helper utilities for the Connexity SDK.

This module provides a small async-friendly wrapper around the Twilio REST
client to fetch call metadata (duration, recording URL, start time).

Notes:
- Twilio's API responses can be eventually consistent (e.g., recordings may not
  be immediately available), so recording lookup supports retries on 404.
- These methods do not raise on Twilio errors; they log and return `None`.
"""

from __future__ import annotations

from asyncio import sleep

from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from connexity.utils.logging_config import get_logger

logger = get_logger(__name__)


class TwilioCallManager:
    """Convenience wrapper for retrieving Twilio call metadata.

    Args:
        client: An initialized Twilio REST `Client`.

    Attributes:
        client: Stored Twilio client.
        account_sid: Twilio Account SID (derived from the client username).
    """

    def __init__(self, client: Client) -> None:
        self.client: Client = client
        self.account_sid: str = client.username

    async def get_call_duration(self, call_sid: str) -> float | None:
        """Fetch the call duration in seconds.

        On any issue, logs and returns `None`.

        Args:
            call_sid: Twilio call SID.

        Returns:
            The call duration as a float (seconds) if available; otherwise `None`.
        """
        try:
            call = self.client.calls(call_sid).fetch()
            return float(call.duration)
        except TwilioRestException as e:
            logger.warning(f"Error fetching call duration [{e.status}]: {e.msg}")
        except Exception as e:
            logger.error(
                f"Unexpected issue fetching call duration: {e}",
                exc_info=True,
            )
        return None

    async def get_call_recording_url(
        self, call_sid: str, *, max_retries: int = 3, delay_sec: int = 3
    ) -> str | None:
        """Fetch the most recent recording URL for a call.

        Twilio may return 404 while the recording is still being processed.
        This method retries up to `max_retries` times when it receives a 404.

        Args:
            call_sid: Twilio call SID.
            max_retries: Maximum number of attempts.
            delay_sec: Delay between attempts (seconds).

        Returns:
            A WAV recording URL string if found; otherwise `None`.
        """
        for attempt in range(1, max_retries + 1):
            try:
                recordings = self.client.recordings.list(call_sid=call_sid)
                if recordings:
                    return f"{recordings[0].media_url}.wav"
            except TwilioRestException as e:
                if e.status == 404:
                    logger.debug(
                        f"Attempt {attempt} got 404; retrying in {delay_sec}s…"
                    )
                else:
                    logger.warning(f"Unexpected issue fetching recording URL: {e}")
                    return None

                if attempt < max_retries:
                    await sleep(delay_sec)
        logger.warning(f"Giving up after {max_retries} attempts to fetch recording URL")
        return None

    async def get_start_call_data(self, call_sid: str) -> str | None:
        """Fetch the call start time as an ISO-8601 string.

        The timestamp is normalized to a `Z` suffix when it is UTC.
        On any issue, logs and returns `None`.

        Args:
            call_sid: Twilio call SID.

        Returns:
            The call start time in ISO-8601 format, or `None` on issue.
        """
        try:
            call = self.client.calls(call_sid).fetch()
            return call.start_time.isoformat().replace("+00:00", "Z")
        except TwilioRestException as e:
            logger.warning(f"Error fetching start time [{e.status}]: {e.msg}")
        except Exception as e:
            logger.error(
                f"Unexpected issue fetching start time: {e}",
                exc_info=True,
            )
        return None

    async def get_call_info(self, call_sid: str) -> dict[str, str] | None:
        """Fetch call information including from and to phone numbers.

        Args:
            call_sid: Twilio call SID.

        Returns:
            A dictionary with 'from', 'to', and 'direction' keys if available;
            otherwise `None`.
        """
        try:
            call = self.client.calls(call_sid).fetch()
            return {
                "from": call._from,
                "to": call.to,
                "direction": call.direction,
            }
        except TwilioRestException as e:
            logger.warning(f"Error fetching call info [{e.status}]: {e.msg}")
        except Exception as e:
            logger.error(
                f"Unexpected issue fetching call info: {e}",
                exc_info=True,
            )
        return None
