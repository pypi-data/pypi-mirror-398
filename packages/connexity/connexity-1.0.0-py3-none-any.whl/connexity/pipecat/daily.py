"""
Daily.co observer implementation for Connexity SDK.

This module provides the ConnexityDailyObserver class for tracking
call sessions that use Daily.co as the communication platform.
"""

from typing import Any, Literal

from pipecat.audio.vad.vad_analyzer import VADParams

from connexity.pipecat.base_observer import BaseConnexityObserver
from connexity.pipecat.utils.get_daily_recording_url import get_daily_recording_url
from connexity.utils.logging_config import LogLevel, get_logger

logger = get_logger(__name__)


class ConnexityDailyObserver(BaseConnexityObserver):
    """
    Observer for Daily.co-based call sessions.

    This observer integrates with Daily.co's API to collect
    call recordings and duration for Connexity analytics.

    Example:
        observer = ConnexityDailyObserver()
        await observer.initialize(
            sid="room-123",
            agent_id="agent-456",
            api_key="connexity-api-key",
            vad_params=vad_params,
            run_mode="production",
            vad_analyzer="silero",
            daily_api_key="daily-api-key",
            log_level=LogLevel.INFO,
        )
    """

    def __init__(self) -> None:
        super().__init__()
        self.daily_api_key: str | None = None

    async def initialize(
        self,
        sid: str,
        agent_id: str,
        api_key: str,
        vad_params: VADParams,
        run_mode: Literal["development", "production"],
        vad_analyzer: str,
        daily_api_key: str,
        log_level: LogLevel | str | int | None = None,
        latency_threshold_ms: float | None = 4000.0,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the Daily.co observer.

        Args:
            sid: Unique session/room identifier
            agent_id: Identifier for the AI agent
            api_key: Connexity API key
            vad_params: Voice Activity Detection parameters
            run_mode: Environment mode ("development" or "production")
            vad_analyzer: VAD analyzer identifier
            daily_api_key: Daily.co API key (required)
            log_level: Logging verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            latency_threshold_ms: Maximum latency threshold in ms (optional)
            **kwargs: Additional keyword arguments (ignored, logged as warning)

        Note:
            Daily.co calls are always treated as "web" type with no phone numbers.
        """
        logger.debug("Initializing Daily observer for session: %s", sid)

        if kwargs:
            logger.warning(
                "Unexpected keyword arguments provided to initialize() | args=%s | "
                "These will be ignored.",
                list(kwargs.keys()),
            )

        try:
            if not daily_api_key:
                raise ValueError("daily_api_key is required")

            # Common setup
            await self._setup_common(
                sid=sid,
                agent_id=agent_id,
                api_key=api_key,
                call_type="web",
                vad_params=vad_params,
                run_mode=run_mode,
                vad_analyzer=vad_analyzer,
                voice_engine="daily",
                phone_call_provider="daily",
                user_phone_number=None,
                agent_phone_number=None,
                log_level=log_level,
                latency_threshold_ms=latency_threshold_ms,
            )

            # Daily-specific setup
            self.daily_api_key = daily_api_key
            self._initialized = True
            logger.info("Daily observer initialized for session: %s", sid)

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
        Collect and send post-call data from Daily.co.

        Retrieves the call recording URL and duration from Daily.co's API
        and sends the complete session data to Connexity.
        """
        if self._initialization_failed:
            logger.debug(
                "Skipping post_process_data: observer initialization previously failed"
            )
            return

        if not self._initialized:
            logger.warning("Skipping post_process_data: observer was not initialized")
            return

        logger.debug("Fetching recording data from Daily.co for session: %s", self.sid)

        try:
            recording_url, duration = get_daily_recording_url(
                self.daily_api_key, self.sid
            )

            logger.debug(
                "Retrieved Daily.co recording for session %s: duration=%ss, has_url=%s",
                self.sid,
                duration,
                bool(recording_url),
            )

            await self.call.init_post_call_data(
                recording_url=recording_url,
                created_at=None,
                duration_in_seconds=duration,
            )

            logger.info(
                "Post-call data successfully submitted for session: %s", self.sid
            )

        except Exception as e:
            logger.error(
                "Failed to process post-call data for session %s (%s): %s",
                self.sid,
                type(e).__name__,
                e,
                exc_info=True,
            )
