"""
Twilio observer implementation for Connexity SDK.

This module provides the ConnexityTwilioObserver class for tracking
call sessions that use Twilio as the telephony provider.

The observer collects call recordings, duration, and metadata for
Connexity analytics by integrating with Twilio's telephony services.
"""

from __future__ import annotations

import asyncio
from typing import Any, Literal

from pipecat.audio.vad.vad_analyzer import VADParams
from twilio.rest import Client

from connexity.pipecat.base_observer import BaseConnexityObserver
from connexity.pipecat.utils.twilio_module import TwilioCallManager
from connexity.utils.logging_config import LogLevel, get_logger

logger = get_logger(__name__)


class ConnexityTwilioObserver(BaseConnexityObserver):
    """
    Observer for Twilio-based call sessions.

    This observer integrates with Twilio's telephony services to collect
    call recordings, duration, and other metadata for Connexity analytics.

    Attributes:
        twilio_client: Manager for Twilio API interactions, set during initialization.

    Example:
        observer = ConnexityTwilioObserver()
        await observer.initialize(
            sid="call-123",
            agent_id="agent-456",
            api_key="connexity-api-key",
            vad_params=vad_params,
            run_mode="production",
            vad_analyzer="silero",
            twilio_client=twilio_client,
            log_level=LogLevel.INFO,
        )

        # After call completion
        await observer.post_process_data()
    """

    __slots__ = ("twilio_client",)

    def __init__(self) -> None:
        super().__init__()
        self.twilio_client: TwilioCallManager | None = None

    async def initialize(
        self,
        sid: str,
        agent_id: str,
        api_key: str,
        vad_params: VADParams,
        run_mode: Literal["development", "production"],
        vad_analyzer: str,
        twilio_client: Client,
        log_level: LogLevel | str | int | None = None,
        latency_threshold_ms: float | None = 4000.0,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the Twilio observer.

        Sets up the observer with session configuration and Twilio client
        for subsequent call tracking and post-processing.

        Args:
            sid: Unique session/call identifier (Twilio Call SID).
            agent_id: Identifier for the AI agent handling the call.
            api_key: Connexity API key for authentication.
            vad_params: Voice Activity Detection parameters for speech analysis.
            run_mode: Environment mode ("development" or "production").
            vad_analyzer: VAD analyzer identifier (e.g., "silero").
            twilio_client: Initialized Twilio REST client (required).
            log_level: Logging verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            latency_threshold_ms: Maximum acceptable latency threshold in ms (optional).
            **kwargs: Additional keyword arguments (ignored, logged as warning).

        Returns:
            None. Sets internal state flags (_initialized, _initialization_failed).

        Note:
            If initialization fails, the observer will be disabled and subsequent
            calls to post_process_data() will return early without processing.
            Call type is automatically derived from Twilio's call direction.
        """
        logger.debug(
            "Initializing Twilio observer for sid=%s, agent_id=%s", sid, agent_id
        )

        if kwargs:
            logger.warning(
                "Unexpected keyword arguments provided to initialize() | args=%s | "
                "These will be ignored.",
                list(kwargs.keys()),
            )

        try:
            if twilio_client is None:
                raise ValueError("twilio_client is required")

            self.twilio_client = TwilioCallManager(twilio_client)

            call_info = await self.twilio_client.get_call_info(sid)
            if not call_info:
                raise ValueError(f"Failed to fetch call info from Twilio for sid={sid}")


            twilio_direction = call_info.get("direction", "").lower()
            if twilio_direction == "inbound":
                call_type: Literal["inbound", "outbound"] = "inbound"
            elif twilio_direction.startswith("outbound"):
                call_type = "outbound"
            else:
                raise ValueError(
                    f"Unexpected Twilio call direction: {twilio_direction} for sid={sid}"
                )

            user_phone_number: str | None = None
            agent_phone_number: str | None = None

            if call_type == "inbound":
                agent_phone_number = call_info.get("to")
                user_phone_number = call_info.get("from")
            else:
                agent_phone_number = call_info.get("from")
                user_phone_number = call_info.get("to")

            # Common setup from base class
            await self._setup_common(
                sid=sid,
                agent_id=agent_id,
                api_key=api_key,
                call_type=call_type,
                vad_params=vad_params,
                run_mode=run_mode,
                vad_analyzer=vad_analyzer,
                voice_engine="pipecat",
                phone_call_provider="twilio",
                user_phone_number=user_phone_number,
                agent_phone_number=agent_phone_number,
                log_level=log_level,
                latency_threshold_ms=latency_threshold_ms,
            )

            self._initialized = True

            logger.info(
                "Twilio observer initialized successfully for sid=%s, call_type=%s, run_mode=%s",
                sid,
                call_type,
                run_mode,
            )

        except TypeError as e:
            self._initialization_failed = True
            logger.error(
                "Initialization failed due to type error | error=%s | "
                "Observer will be disabled. Customer's agent will continue without observability.",
                e,
                exc_info=True,
            )

        except ValueError as e:
            self._initialization_failed = True
            logger.error(
                "Initialization failed due to invalid parameters | error=%s | "
                "Observer will be disabled. Customer's agent will continue without observability.",
                e,
            )

        except Exception as e:
            self._initialization_failed = True
            logger.error(
                "Initialization failed unexpectedly | sid=%s | error_type=%s | error=%s | "
                "Observer will be disabled. Customer's agent will continue without observability.",
                sid,
                type(e).__name__,
                e,
                exc_info=True,
            )

    async def post_process_data(self) -> None:
        """
        Collect and send post-call data from Twilio.

        Retrieves the call recording URL, creation time, and duration
        from Twilio's API concurrently and sends the complete session
        data to Connexity for analytics.

        This method should be called after the call has ended to finalize
        the session data collection.

        Returns:
            None. Data is sent to Connexity via the internal call object.

        Note:
            - This method returns early if initialization failed or was not completed.
            - Twilio API calls are made concurrently for optimal performance.
            - Recording availability may be delayed; consider retry logic if needed.
        """
        # Early exit checks with appropriate logging
        if self._initialization_failed:
            logger.debug("Skipping post_process_data: initialization previously failed")
            return

        if not self._initialized:
            logger.debug("Skipping post_process_data: observer not initialized")
            return

        if self.twilio_client is None:
            logger.warning(
                "Skipping post_process_data for sid=%s: twilio_client is None despite initialization",
                self.sid,
            )
            return

        logger.debug("Starting post-call data collection for sid=%s", self.sid)

        try:
            # Fetch call data concurrently for better performance
            # These three API calls are independent and can run in parallel
            recording_url, created_at, duration = await asyncio.gather(
                self.twilio_client.get_call_recording_url(self.sid),
                self.twilio_client.get_start_call_data(self.sid),
                self.twilio_client.get_call_duration(self.sid),
            )

            logger.debug(
                "Retrieved Twilio call data for sid=%s: duration=%ss, has_recording=%s",
                self.sid,
                duration,
                bool(recording_url),
            )

            await self.call.init_post_call_data(
                recording_url=recording_url,
                created_at=created_at,
                duration_in_seconds=duration,
            )

            logger.info("Post-call data successfully sent for sid=%s", self.sid)

        except Exception as e:
            logger.error(
                "Failed to process post-call data for sid=%s (%s): %s",
                self.sid,
                type(e).__name__,
                e,
                exc_info=True,
            )
