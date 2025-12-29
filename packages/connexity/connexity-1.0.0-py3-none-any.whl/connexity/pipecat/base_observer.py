"""
Pipecat frame observer for the Connexity SDK.

This module provides a base observer class that monitors Pipecat frame events
to capture conversation data, track latency metrics, detect interruptions,
and report issues to the Connexity backend.

Key Features:
    - Conversation capture: Records user/assistant messages with timing
    - Latency tracking: Measures STT, LLM, TTS, and end-to-end latency
    - Interruption detection: Identifies unsuccessful user interruptions
    - Overlap tracking: Detects and analyzes speech overlaps
    - Tool call monitoring: Tracks function call lifecycle and issues
    - Issue reporting: Automatically reports latency peaks and errors

Usage:
    Subclass BaseConnexityObserver and implement the provider-specific
    initialize() and post_process_data() methods.

Example:
    class MyObserver(BaseConnexityObserver):
        async def initialize(self, sid: str, agent_id: str, ...):
            await self._setup_common(sid, agent_id, ...)

        async def post_process_data(self):
            # Collect provider-specific data (recordings, etc.)
            await self.call.init_post_call_data(...)
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Final, Literal

from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import (
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
    CancelFrame,
    EndFrame,
    ErrorFrame,
    FunctionCallInProgressFrame,
    FunctionCallResultFrame,
    LLMFullResponseStartFrame,
    TranscriptionFrame,
    TTSStartedFrame,
    TTSTextFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
)
from pipecat.observers.base_observer import BaseObserver, FramePushed
from pipecat.processors.frame_processor import FrameDirection
from pipecat.services.llm_service import LLMService
from pipecat.services.stt_service import STTService
from pipecat.services.tts_service import TTSService

from connexity.calls.call_session import CallSession
from connexity.calls.messages.assistant_message import AssistantMessage
from connexity.calls.messages.issue_message import IssueMessage
from connexity.calls.messages.tool_call_message import ToolCallMessage
from connexity.calls.messages.tool_result_message import ToolResultMessage
from connexity.calls.messages.user_message import UserMessage
from connexity.pipecat.tool_observer import ToolExecutionContext, ToolObserverRegistry
from connexity.pipecat.utils.detect_interruption_loops import detect_interruption_loops
from connexity.pipecat.utils.observer_utils import (
    apply_min_separation,
    extract_model_voice,
    find_by_class_name,
    get_switcher_active_service,
    guess_provider,
    is_downstream_output,
    ns_to_s,
    trace_upstream,
)
from connexity.utils.logging_config import LogLevel, get_logger, set_sdk_log_level
from connexity.utils.snapshot_error_frame import (
    _extract_schema_from_entry,
    _schema_to_json,
    snapshot_error_frame,
)

# Module-level logger instance
logger = get_logger(__name__)

# Type alias for message roles in conversation tracking
Role = Literal["user", "assistant", "tool_call"]

# Service family types for timeline updates
ServiceFamily = Literal["stt", "llm", "tts"]

# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------


@dataclass
class Latency:
    """
    Container for latency measurements across the audio processing pipeline.

    Tracks time intervals between pipeline stages in milliseconds.
    Used to identify bottlenecks and performance issues.

    Attributes:
        tts: Time for TTS processing (LLM response to audio ready).
        llm: Time for LLM inference (first token latency).
        stt: Time for STT processing (audio to transcript).
        vad: VAD delay compensation (configured stop_secs value).
    """

    tts: float | None = None
    llm: float | None = None
    stt: float | None = None
    vad: float | None = None

    def get_metrics(self) -> dict[str, float | None]:
        """
        Return latency values as a dictionary for serialization.

        Returns:
            Dictionary mapping latency type names to their values in milliseconds.
            Keys are: 'tts', 'llm', 'stt', 'vad'.
        """
        return {"tts": self.tts, "llm": self.llm, "stt": self.stt, "vad": self.vad}


@dataclass
class MessageData:
    """
    Data container for a message (user or assistant) being accumulated.

    Tracks the timing window and content of a single utterance as frames
    are processed. Once complete, data is flushed to the Connexity backend.

    Attributes:
        role: Message role - "user" or "assistant".
        start: Utterance start time (seconds from call start).
        end: Utterance end time (seconds from call start).
        content: Accumulated text content.
        latency: Associated latency metrics (assistant messages only).
    """

    role: Role
    start: float | None = None
    end: float | None = None
    content: str = ""
    latency: Latency | None = None

    def has_valid_window(self) -> bool:
        """
        Check if this message has valid timing and content for flushing.

        A message is valid when:
        - Both start and end times are set
        - Content is non-empty after stripping whitespace
        - Start time is before end time

        Returns:
            True if the message can be flushed to the backend.
        """
        return (
            self.start is not None
            and self.end is not None
            and self.content.strip() != ""
            and self.start < self.end
        )

    def reset(self) -> None:
        """
        Reset message data for the next utterance.

        Clears timing, content, and latency data while preserving role.
        """
        self.start = None
        self.end = None
        self.content = ""
        if self.latency is not None:
            self.latency = Latency()

    def get_metrics(self) -> dict[str, Any]:
        """
        Return message data as a dictionary for metrics collection.

        Returns:
            Dictionary containing role, timing, content, and latency data.
        """
        return {
            "role": self.role,
            "start": self.start,
            "end": self.end,
            "content": self.content,
            "latency": self.latency,
        }


@dataclass
class ToolCallData:
    """
    Data container for an in-progress tool/function call.

    Tracks the tool call lifecycle including timing, arguments, and results.
    Used to correlate FunctionCallInProgressFrame with FunctionCallResultFrame.

    Attributes:
        role: Always "tool_call" for this data type.
        start: Tool call start time (seconds from call start).
        end: Tool call end time (seconds from call start).
        tool_call_id: Unique identifier for this tool call.
        function_name: Name of the function being called.
        arguments: JSON-encoded function arguments.
        content: Result content from the function.
    """

    role: Role = "tool_call"
    start: float | None = None
    end: float | None = None
    tool_call_id: str | None = None
    function_name: str | None = None
    arguments: str | None = None
    content: str = ""


@dataclass
class InterruptionAttempt:
    """
    Tracks a user interruption attempt while the bot is speaking.

    Used to detect unsuccessful interruptions where the bot continues
    speaking despite meaningful user input. An interruption is considered
    unsuccessful if the user spoke enough words or for long enough, but
    no CancelFrame was issued to stop the bot.

    Attributes:
        start: Interruption start timestamp (seconds from call start).
        stt_words: Count of transcribed words during the attempt.
        first_transcript_at: Timestamp of first transcription during overlap.
        saw_cancel: Whether a CancelFrame was received.
        user_stop: Timestamp when user stopped speaking.
        bot_stop: Timestamp when bot stopped speaking.
    """

    start: float
    stt_words: int = 0
    first_transcript_at: float | None = None
    saw_cancel: bool = False
    user_stop: float | None = None
    bot_stop: float | None = None


# ---------------------------------------------------------------------------
# Main Observer Class
# ---------------------------------------------------------------------------


class BaseConnexityObserver(BaseObserver):
    """
    Base Pipecat observer for Connexity SDK integration.

    Monitors frame events to capture conversation data, track latency metrics,
    detect interruptions and overlaps, and report issues to the Connexity backend.

    This class implements the core observation logic. Subclasses should implement:
        - initialize(): Provider-specific setup that calls _setup_common()
        - post_process_data(): Post-call data collection (recordings, duration)

    Class Attributes:
        MIN_SEPARATION: Minimum time gap (seconds) between consecutive events
            to avoid duplicate registrations from rapid frame bursts.

    Instance Attributes:
        call: The active CallSession for Connexity backend communication.
        user_data: Accumulator for the current user utterance.
        assistant_data: Accumulator for the current assistant response.
        tool_calls: Accumulator for the current tool call data.
        messages: List of all message metrics collected during the call.
        sid: Unique session identifier for this call.
        final: Flag indicating call has been finalized.

    Example:
        >>> class MyObserver(BaseConnexityObserver):
        ...     async def initialize(self, sid, agent_id, api_key, **kwargs):
        ...         await self._setup_common(sid, agent_id, api_key, **kwargs)
        ...
        ...     async def post_process_data(self):
        ...         recording_url = await get_recording()
        ...         await self.call.init_post_call_data(recording_url=recording_url)
    """

    # Minimum time separation between events to prevent duplicates
    MIN_SEPARATION: Final[float] = 0.5

    def __init__(self) -> None:
        """Initialize the observer with default state."""
        super().__init__()

        # Core session state
        self.call: CallSession | None = None
        self.sid: str | None = None
        self.final: bool = False

        # Message accumulators
        self.user_data: MessageData = MessageData(role="user")
        self.assistant_data: MessageData = MessageData(
            role="assistant", latency=Latency()
        )
        self.tool_calls: ToolCallData = ToolCallData()
        self.messages: list[dict[str, Any]] = []

        # Latency tracking timestamps (seconds from call start)
        self.stt_start: float | None = None
        self.tts_start: float | None = None
        self.llm_start: float | None = None
        self.vad_stop_secs: float | None = None
        self.vad_start_secs: float | None = None

        # Interruption detection state
        self._bot_speaking: bool = False
        self._current_user_is_interruption: bool = False
        self._active_interrupt: InterruptionAttempt | None = None
        self.INTERRUPT_MIN_WORDS: int = 3
        self.INTERRUPT_MIN_OVERLAP_SECS: float = 1.0
        self.INTERRUPT_EXPECT_CANCEL_WITHIN_SECS: float = 3.0

        # Overlap tracking for interruption loop detection
        self._overlap_active: bool = False
        self._overlap_start_ts: float | None = None
        self._overlap_user_words: int = 0
        self._overlap_bot_words: int = 0
        self._overlap_interrupter: str | None = None
        self._overlap_first_transcript_at: float | None = None
        self._overlaps_summary: list[dict[str, Any]] = []

        # User VAD de-duplication state
        self._user_speaking: bool = False
        self._last_user_start_ts: float | None = None
        self._last_user_stop_ts: float | None = None
        self.USER_EVENT_DEDUP_SECS: float = 0.1

        # Background task tracking for async issue registration
        self._pending_issue_tasks: list[asyncio.Task[Any]] = []

        # Initialization state flags
        self._initialized: bool = False
        self._initialization_failed: bool = False

        # Tool execution observability registry
        self._tool_observer_registry: ToolObserverRegistry = (
            ToolObserverRegistry.get_instance()
        )

        # Logging configuration
        self._log_level: LogLevel = LogLevel.WARNING

        # Latency threshold for peak detection (milliseconds)
        self.latency_threshold_ms: float = 4000.0

        # Message ID tracking for issue association
        self._last_assistant_message_id: str | None = None
        self._last_user_message_id: str | None = None
        self._last_tool_call_message_id: str | None = None
        self._tool_call_id_to_message_id: dict[str, str] = {}

        # Content accumulation buffers (optimized for string building)
        self._user_content_buffer: list[str] = []
        self._assistant_content_buffer: list[str] = []

    # -----------------------------------------------------------------------
    # Configuration Methods
    # -----------------------------------------------------------------------

    def _configure_logging(self, log_level: LogLevel | str | int | None = None) -> None:
        """
        Configure the logging level for this observer and the SDK.

        Sets the log verbosity for all Connexity SDK components. Higher verbosity
        levels include more detailed operational information.

        Args:
            log_level: The desired log level. Accepts:
                - LogLevel enum value (e.g., LogLevel.DEBUG)
                - String: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
                - Integer: 10, 20, 30, 40, 50 (standard logging levels)
                - None: Use default (WARNING)

        Note:
            Log levels follow standard Python logging:
            - DEBUG (10): Detailed operational info, latency metrics
            - INFO (20): Significant events (function calls, message flush)
            - WARNING (30): Actionable issues (latency peaks, interruptions)
            - ERROR (40): Failures requiring attention
            - CRITICAL (50): Severe failures
        """
        if log_level is None:
            self._log_level = LogLevel.WARNING
        elif isinstance(log_level, LogLevel):
            self._log_level = log_level
        elif isinstance(log_level, str):
            level_map: dict[str, LogLevel] = {
                "DEBUG": LogLevel.DEBUG,
                "INFO": LogLevel.INFO,
                "WARNING": LogLevel.WARNING,
                "ERROR": LogLevel.ERROR,
                "CRITICAL": LogLevel.CRITICAL,
            }
            self._log_level = level_map.get(log_level.upper(), LogLevel.WARNING)
        elif isinstance(log_level, int):
            try:
                self._log_level = LogLevel(log_level)
            except ValueError:
                self._log_level = LogLevel.WARNING
        else:
            self._log_level = LogLevel.WARNING

        set_sdk_log_level(self._log_level)

    async def _setup_common(
        self,
        sid: str,
        agent_id: str,
        api_key: str,
        call_type: Literal["inbound", "outbound", "web"],
        vad_params: VADParams,
        run_mode: Literal["development", "production"],
        vad_analyzer: str,
        voice_engine: str,
        phone_call_provider: str | None = None,
        user_phone_number: str | None = None,
        agent_phone_number: str | None = None,
        log_level: LogLevel | str | int | None = None,
        latency_threshold_ms: float | None = 4000.0,
    ) -> None:
        """
        Perform common initialization for all observer subclasses.

        This method sets up logging, stores VAD parameters, and registers
        the call session with the Connexity backend. Should be called from
        subclass initialize() implementations.

        Args:
            sid: Unique session identifier for this call.
            agent_id: Identifier for the AI agent handling the call.
            api_key: Connexity API key for authentication.
            call_type: Type of call - "inbound", "outbound", or "web".
            vad_params: Voice Activity Detection parameters from Pipecat.
            run_mode: Environment mode - "development" or "production".
            vad_analyzer: VAD analyzer identifier string.
            voice_engine: Voice processing engine ("pipecat" or "daily").
            phone_call_provider: Optional telephony provider name.
            user_phone_number: Optional user's phone number (E.164 format).
            agent_phone_number: Optional agent's phone number (E.164 format).
            log_level: Optional logging verbosity level.
            latency_threshold_ms: Threshold (ms) for latency peak detection.
                Defaults to 4000ms. Set to None to disable peak detection.

        Raises:
            Exception: If call registration with Connexity backend fails.
        """
        from connexity.client import ConnexityClient

        self._configure_logging(log_level=log_level)

        self.sid = sid
        self.vad_stop_secs = vad_params.stop_secs
        self.vad_start_secs = vad_params.start_secs
        self.latency_threshold_ms = latency_threshold_ms

        connexity_client = ConnexityClient(api_key=api_key)
        self.call = await connexity_client.register_call(
            sid=sid,
            agent_id=agent_id,
            user_phone_number=user_phone_number,
            agent_phone_number=agent_phone_number,
            created_at=None,
            voice_engine=voice_engine,
            call_type=call_type,
            phone_call_provider=phone_call_provider,
            run_mode=run_mode,
            vad_analyzer=vad_analyzer,
        )

    # -----------------------------------------------------------------------
    # Service Timeline Updates
    # -----------------------------------------------------------------------

    async def _update_service_timeline(
        self,
        frame: Any,
        src: Any,
        direction: FrameDirection,
        t: float,
    ) -> None:
        """
        Update the service timeline when a relevant frame is processed.

        Detects STT, LLM, and TTS services in the processor chain and
        registers their provider/model/voice info with the call session.
        This enables tracking of which services were used at what times.

        Args:
            frame: The Pipecat frame being processed.
            src: The frame source processor.
            direction: Frame propagation direction.
            t: Current timestamp (seconds from call start).
        """
        upstream_nodes = trace_upstream(src)

        # Service families to track: (family, service_class, should_process, include_voice)
        families: list[tuple[ServiceFamily, type, bool, bool]] = [
            (
                "stt",
                STTService,
                isinstance(frame, TranscriptionFrame),
                False,
            ),
            (
                "llm",
                LLMService,
                isinstance(frame, LLMFullResponseStartFrame)
                and is_downstream_output(src, direction),
                False,
            ),
            (
                "tts",
                TTSService,
                isinstance(frame, TTSStartedFrame)
                and is_downstream_output(src, direction),
                True,
            ),
        ]

        for family, service_cls, should_process, include_voice in families:
            if not should_process:
                continue

            provider: str | None = None
            model: str | None = None
            voice: str | None = None

            # First check ServiceSwitchers for the active service
            switchers = find_by_class_name(upstream_nodes, "ServiceSwitcher")
            for sw in switchers:
                active = get_switcher_active_service(sw)
                if active and isinstance(active, service_cls):
                    provider = guess_provider(active)
                    m, v = extract_model_voice(active)
                    model = m
                    if include_voice:
                        voice = v
                    break

            # Fallback: search for direct service instances
            if provider is None and model is None:
                nodes = find_by_class_name(upstream_nodes, service_cls.__name__)
                node = nodes[0] if nodes else None
                if node:
                    provider = guess_provider(node)
                    m, v = extract_model_voice(node)
                    model = m
                    if include_voice:
                        voice = v

            # Register timeline update if we found any info
            if (
                provider is not None
                or model is not None
                or (include_voice and voice is not None)
            ):
                if family == "tts":
                    await self.call.update_service_timeline(
                        "tts",
                        provider=provider,
                        model=model,
                        voice=voice,
                        at_seconds=t,
                    )
                else:
                    await self.call.update_service_timeline(
                        family,
                        provider=provider,
                        model=model,
                        at_seconds=t,
                    )

    # -----------------------------------------------------------------------
    # Latency Tracking
    # -----------------------------------------------------------------------

    def _handle_latency_markers(
        self,
        frame: Any,
        src: Any,
        direction: FrameDirection,
        t: float,
    ) -> None:
        """
        Track latency anchor points from relevant frames.

        Measures time intervals between pipeline stages and records them
        in the assistant latency data. The latency pipeline is:
        UserStopped -> STT -> LLM -> TTS -> BotStarted

        Args:
            frame: The Pipecat frame being processed.
            src: The frame source processor.
            direction: Frame propagation direction.
            t: Current timestamp (seconds from call start).
        """
        # User finished speaking -> STT processing begins
        if isinstance(frame, UserStoppedSpeakingFrame):
            self.stt_start = t

        # LLM response begins (first token) -> close STT latency window
        if (
            isinstance(frame, LLMFullResponseStartFrame)
            and is_downstream_output(src, direction)
            and self.stt_start is not None
            and self.assistant_data.latency.stt is None
        ):
            self.llm_start = t
            stt_ms = (t - self.stt_start) * 1000
            self.assistant_data.latency.stt = stt_ms
            self.stt_start = None

            logger.debug("STT latency recorded | ms=%.2f", stt_ms)

        # TTS starts processing -> close LLM latency window
        if (
            isinstance(frame, TTSStartedFrame)
            and is_downstream_output(src, direction)
            and self.tts_start is None
        ):
            if self.llm_start is not None:
                llm_ms = (t - self.llm_start) * 1000
                self.assistant_data.latency.llm = llm_ms

                logger.debug("LLM latency recorded | ms=%.2f", llm_ms)

            self.tts_start = t

        # Bot audio playback starts -> close TTS preparation latency
        if (
            isinstance(frame, BotStartedSpeakingFrame)
            and is_downstream_output(src, direction)
            and self.tts_start
        ):
            tts_ms = (t - self.tts_start) * 1000
            self.assistant_data.latency.tts = tts_ms
            self.tts_start = None

            logger.debug("TTS latency recorded | ms=%.2f", tts_ms)

        # Cancel frame during active interruption attempt
        if (
            isinstance(frame, CancelFrame)
            and is_downstream_output(src, direction)
            and self._active_interrupt
            and self._bot_speaking
        ):
            self._active_interrupt.saw_cancel = True

            logger.debug("Cancel frame during interruption | t=%.3f", t)

    # -----------------------------------------------------------------------
    # Speaking Window Management
    # -----------------------------------------------------------------------

    def _handle_bot_window(
        self,
        frame: Any,
        src: Any,
        direction: FrameDirection,
        t: float,
    ) -> None:
        """
        Handle bot speaking window start/stop events.

        Updates the assistant message timing window and manages overlap
        tracking when both user and bot are speaking.

        Args:
            frame: The Pipecat frame being processed.
            src: The frame source processor.
            direction: Frame propagation direction.
            t: Current timestamp (seconds from call start).
        """
        if not is_downstream_output(src, direction):
            return

        if isinstance(frame, BotStartedSpeakingFrame):
            self._bot_speaking = True

            # Start overlap tracking if user is already speaking
            if self._user_speaking and not self._overlap_active:
                self._start_overlap(t, interrupter="bot")

            self.assistant_data.start = apply_min_separation(
                self.assistant_data.start, t, self.MIN_SEPARATION
            )

            logger.debug("Bot started speaking | t=%.3f", t)

        elif isinstance(frame, BotStoppedSpeakingFrame):
            self.assistant_data.end = apply_min_separation(
                self.assistant_data.end, t, self.MIN_SEPARATION
            )
            logger.debug("Bot stopped speaking | t=%.3f", t)

            if self._active_interrupt:
                self._finalize_interrupt_attempt(t, "bot_stopped")

            if self._overlap_active:
                self._end_overlap(t)

            self._bot_speaking = False

    def _handle_user_window(
        self,
        frame: Any,
        src: Any,
        direction: FrameDirection,
        t: float,
    ) -> None:
        """
        Handle user speaking window start/stop events.

        Updates the user message timing window and manages interruption
        and overlap detection when user speaks while bot is speaking.

        Args:
            frame: The Pipecat frame being processed.
            src: The frame source processor.
            direction: Frame propagation direction.
            t: Current timestamp (seconds from call start).
        """
        if isinstance(frame, UserStartedSpeakingFrame):
            # De-duplicate rapid start events
            if self._user_speaking:
                if (
                    self._last_user_start_ts is not None
                    and (t - self._last_user_start_ts) < self.USER_EVENT_DEDUP_SECS
                ):
                    return
                return

            self._user_speaking = True
            self._last_user_start_ts = t

            # Compensate for VAD pre-roll to approximate true speech start
            vad_start = t
            true_start = vad_start - (self.vad_start_secs or 0.0)
            self.user_data.start = true_start

            if self._bot_speaking:
                self._current_user_is_interruption = True
                self._start_interrupt_attempt(true_start)
                if not self._overlap_active:
                    self._start_overlap(true_start, interrupter="user")
            else:
                self._current_user_is_interruption = False

            logger.debug(
                "User started speaking | t=%.3f | true_start=%.3f | is_interruption=%s",
                t,
                true_start,
                self._current_user_is_interruption,
            )

        elif isinstance(frame, UserStoppedSpeakingFrame):
            # De-duplicate rapid stop events
            if not self._user_speaking:
                if (
                    self._last_user_stop_ts is not None
                    and (t - self._last_user_stop_ts) < self.USER_EVENT_DEDUP_SECS
                ):
                    return
                return

            self._user_speaking = False
            self._last_user_stop_ts = t
            self.user_data.end = t

            logger.debug("User stopped speaking | t=%.3f", t)

            if self._active_interrupt:
                self._finalize_interrupt_attempt(t, "user_stopped")

            if self._overlap_active:
                self._end_overlap(t)

    # -----------------------------------------------------------------------
    # Tool Call Handling
    # -----------------------------------------------------------------------

    async def _handle_tool_call_start(
        self,
        frame: Any,
        src: Any,
        direction: FrameDirection,
        t: float,
    ) -> None:
        """
        Handle the start of a function/tool call.

        Registers the tool call message with the Connexity backend and
        stores the mapping between tool_call_id and message_id.

        Args:
            frame: The Pipecat frame being processed.
            src: The frame source processor.
            direction: Frame propagation direction.
            t: Current timestamp (seconds from call start).
        """
        if not (
            isinstance(frame, FunctionCallInProgressFrame)
            and is_downstream_output(src, direction)
        ):
            return

        self.tool_calls.start = apply_min_separation(
            self.tool_calls.start, t, self.MIN_SEPARATION
        )
        self.tool_calls.tool_call_id = frame.tool_call_id
        self.tool_calls.function_name = frame.function_name
        self.tool_calls.arguments = frame.arguments

        tool_call_msg = ToolCallMessage(
            arguments=frame.arguments,
            tool_call_id=frame.tool_call_id,
            content="",
            name=frame.function_name,
            seconds_from_start=t,
        )
        await self.call.register_message(tool_call_msg)
        self._last_tool_call_message_id = tool_call_msg.id
        self._tool_call_id_to_message_id[frame.tool_call_id] = tool_call_msg.id

        logger.info(
            "Tool call started | id=%s | function=%s",
            frame.tool_call_id,
            frame.function_name,
        )

    async def _handle_tool_call_end(
        self,
        frame: Any,
        src: Any,
        direction: FrameDirection,
        t: float,
    ) -> None:
        """
        Handle the completion of a function/tool call.

        Processes execution context from the tool observer registry,
        registers the result message, and reports any execution issues.

        Args:
            frame: The Pipecat frame being processed.
            src: The frame source processor.
            direction: Frame propagation direction.
            t: Current timestamp (seconds from call start).
        """
        if not (
            isinstance(frame, FunctionCallResultFrame)
            and is_downstream_output(src, direction)
        ):
            return

        self.tool_calls.end = apply_min_separation(
            self.tool_calls.end, t, self.MIN_SEPARATION
        )
        self.tool_calls.content = frame.result

        # Convert result to string
        if frame.result is None:
            result_str = None
        elif isinstance(frame.result, (dict, list)):
            result_str = json.dumps(frame.result)
        else:
            result_str = str(frame.result)

        # Retrieve execution context from tool observer
        execution_ctx: (
            ToolExecutionContext | None
        ) = await self._tool_observer_registry.get_execution(frame.tool_call_id)

        logger.debug(
            "Tool execution context retrieved | tool_call_id=%s",
            frame.tool_call_id,
        )

        # Build metadata and handle execution context
        metadata: dict[str, Any] | None = None
        if execution_ctx:
            logger.debug(
                "Execution context | tool=%s | duration_ms=%s | success=%s",
                execution_ctx.tool_name,
                execution_ctx.duration_ms,
                execution_ctx.success,
            )

            # Log execution issues at ERROR level
            if execution_ctx.issue:
                logger.error(
                    "Tool execution failed | tool=%s | error=%s: %s",
                    execution_ctx.tool_name,
                    type(execution_ctx.issue).__name__,
                    execution_ctx.issue,
                )
                if execution_ctx.issue_traceback:
                    # Truncate traceback for debug log
                    tb_preview = (
                        execution_ctx.issue_traceback[:500] + "..."
                        if len(execution_ctx.issue_traceback) > 500
                        else execution_ctx.issue_traceback
                    )
                    logger.debug("Tool execution traceback | traceback=%s", tb_preview)

            metadata = {
                "tool_name": execution_ctx.tool_name,
                "duration_ms": execution_ctx.duration_ms,
                "success": execution_ctx.success,
                "arguments": execution_ctx.arguments,
            }

            # Register execution failure as an issue
            if not execution_ctx.success and execution_ctx.issue:
                tool_call_message_id = self._tool_call_id_to_message_id.get(
                    execution_ctx.tool_call_id
                )
                err = IssueMessage(
                    content=f"Tool execution issue: {execution_ctx.issue}",
                    source="tool_call",
                    message_id=tool_call_message_id,
                    seconds_from_start=execution_ctx.start_time or t,
                    code="tool_execution_issue",
                    metadata={
                        "tool_name": execution_ctx.tool_name,
                        "tool_call_id": execution_ctx.tool_call_id,
                        "arguments": execution_ctx.arguments,
                        "duration_ms": execution_ctx.duration_ms,
                        "issue_type": (
                            type(execution_ctx.issue).__name__
                            if execution_ctx.issue
                            else None
                        ),
                        "issue_message": (
                            str(execution_ctx.issue) if execution_ctx.issue else None
                        ),
                        "issue_traceback": execution_ctx.issue_traceback,
                        "timeout_triggered": execution_ctx.timeout_triggered,
                        "timeout_seconds": (
                            execution_ctx.timeout_seconds
                            if execution_ctx.timeout_triggered
                            else None
                        ),
                    },
                )
                await self.call.register_issue(err)

            # Clean up execution context after processing
            await self._tool_observer_registry.clear_execution(frame.tool_call_id)
        else:
            logger.warning(
                "No execution context found | tool_call_id=%s | "
                "hint=Tool may be missing @observe_tool() decorator",
                frame.tool_call_id,
            )

        # Register the tool result message
        await self.call.register_message(
            ToolResultMessage(
                content="",
                tool_call_id=frame.tool_call_id,
                result=result_str,
                seconds_from_start=t,
                metadata=metadata,
            )
        )

        logger.info(
            "Tool call completed | id=%s | success=%s",
            frame.tool_call_id,
            execution_ctx.success if execution_ctx else "unknown",
        )

    # -----------------------------------------------------------------------
    # Interruption Handling
    # -----------------------------------------------------------------------

    def _start_interrupt_attempt(self, t: float) -> None:
        """
        Begin tracking an interruption attempt.

        Called when the user starts speaking while the bot is still speaking.
        Creates an InterruptionAttempt to track whether the interruption
        is successful (bot stops) or unsuccessful (bot continues).

        Args:
            t: Start timestamp (seconds from call start).
        """
        if self._active_interrupt is None:
            self._active_interrupt = InterruptionAttempt(start=t)
            logger.debug("Interruption attempt started | t=%.3f", t)

    def _finalize_interrupt_attempt(self, t: float, reason: str) -> None:
        """
        Finalize and evaluate an interruption attempt.

        Determines if the interruption was unsuccessful (bot continued
        speaking despite meaningful user input) and registers an issue.

        An interruption is considered unsuccessful when:
        - User spoke enough words (>= INTERRUPT_MIN_WORDS) OR
        - Overlap lasted long enough (>= INTERRUPT_MIN_OVERLAP_SECS)
        AND
        - No CancelFrame was received within INTERRUPT_EXPECT_CANCEL_WITHIN_SECS

        Args:
            t: End timestamp (seconds from call start).
            reason: Reason for finalization:
                - "user_stopped": User stopped speaking
                - "bot_stopped": Bot stopped speaking
                - "call_ending": Call is terminating
        """
        attempt = self._active_interrupt
        if not attempt:
            return

        if reason == "user_stopped" and attempt.user_stop is None:
            attempt.user_stop = t
        if reason == "bot_stopped" and attempt.bot_stop is None:
            attempt.bot_stop = t

        stop_t = attempt.user_stop or attempt.bot_stop or t
        overlap_secs = max(0.0, stop_t - attempt.start)

        # Meaningful attempt: enough words or long enough overlap
        meaningful_attempt = (attempt.stt_words >= self.INTERRUPT_MIN_WORDS) or (
            overlap_secs >= self.INTERRUPT_MIN_OVERLAP_SECS
        )

        # Check if cancel frame was expected but not received
        time_since_start = stop_t - attempt.start
        no_cancel_within_threshold = (not attempt.saw_cancel) and (
            time_since_start >= self.INTERRUPT_EXPECT_CANCEL_WITHIN_SECS
        )

        unsuccessful = meaningful_attempt and no_cancel_within_threshold

        if unsuccessful:
            root_cause = "unknown"
            if (
                attempt.stt_words == 0
                and overlap_secs >= self.INTERRUPT_MIN_OVERLAP_SECS
            ):
                root_cause = "no_transcripts_during_overlap"

            err = IssueMessage(
                content="Unsuccessful user interruption (agent continued speaking)",
                source="observer",
                message_id=self._last_user_message_id,
                seconds_from_start=attempt.start,
                code="unsuccessful_interruption",
                metadata={
                    "attempt": {
                        "start": attempt.start,
                        "user_stop": attempt.user_stop,
                        "bot_stop": attempt.bot_stop,
                        "overlap_secs": overlap_secs,
                        "stt_words": attempt.stt_words,
                        "first_transcript_at": attempt.first_transcript_at,
                        "saw_cancel": attempt.saw_cancel,
                    },
                    "thresholds": {
                        "min_words": self.INTERRUPT_MIN_WORDS,
                        "min_overlap_secs": self.INTERRUPT_MIN_OVERLAP_SECS,
                        "expect_cancel_within_secs": self.INTERRUPT_EXPECT_CANCEL_WITHIN_SECS,
                        "vad_start_secs": self.vad_start_secs,
                        "vad_stop_secs": self.vad_stop_secs,
                    },
                    "root_cause_heuristic": root_cause,
                },
            )

            logger.warning(
                "Unsuccessful interruption | overlap_secs=%.2f | words=%d | root_cause=%s",
                overlap_secs,
                attempt.stt_words,
                root_cause,
            )

            try:
                task = asyncio.create_task(self.call.register_issue(err))
                self._pending_issue_tasks.append(task)
            except Exception:
                pass

        self._active_interrupt = None

    # -----------------------------------------------------------------------
    # Content Accumulation
    # -----------------------------------------------------------------------

    def _accumulate_content(
        self,
        frame: Any,
        src: Any,
        direction: FrameDirection,
        t: float,
    ) -> None:
        """
        Accumulate text content from transcription and TTS frames.

        Appends user speech transcriptions to user_data and bot TTS text
        to assistant_data. Also tracks word counts during overlaps for
        interruption analysis.

        Args:
            frame: The Pipecat frame being processed.
            src: The frame source processor.
            direction: Frame propagation direction.
            t: Current timestamp (seconds from call start).
        """
        # Accumulate STT transcriptions (user speech)
        if (
            isinstance(frame, TranscriptionFrame)
            and getattr(src, "name", "").find("STTService") != -1
        ):
            self.user_data.content += frame.text

            if self._bot_speaking:
                if self._active_interrupt is None:
                    self._start_interrupt_attempt(t)

                words = [w for w in frame.text.strip().split() if w]
                if words and self._active_interrupt:
                    self._active_interrupt.stt_words += len(words)
                    if self._active_interrupt.first_transcript_at is None:
                        self._active_interrupt.first_transcript_at = t

                # Track user words during overlap
                if self._overlap_active and words:
                    self._overlap_user_words += len(words)
                    if (
                        self._overlap_interrupter == "user"
                        and self._overlap_first_transcript_at is None
                    ):
                        self._overlap_first_transcript_at = t

        # Accumulate TTS text (bot speech)
        if isinstance(frame, TTSTextFrame) and is_downstream_output(
            src, direction
        ):
            self.assistant_data.content += frame.text + " "

            # Track bot words during overlap
            if self._overlap_active:
                bot_words = [w for w in (frame.text or "").strip().split() if w]
                if bot_words:
                    self._overlap_bot_words += len(bot_words)

    # -----------------------------------------------------------------------
    # Message Flushing
    # -----------------------------------------------------------------------

    async def _maybe_flush_user(self) -> None:
        """
        Flush accumulated user message data if the window is valid.

        Registers the user message with the Connexity backend and resets
        the accumulator for the next utterance.
        """
        if not self.user_data.has_valid_window():
            return

        self.messages.append(self.user_data.get_metrics())
        user_msg = UserMessage(
            content=self.user_data.content,
            seconds_from_start=self.user_data.start,
            is_interruption=self._current_user_is_interruption,
        )
        await self.call.register_message(user_msg)
        self._last_user_message_id = user_msg.id

        logger.debug(
            "User message flushed | chars=%d | is_interruption=%s",
            len(self.user_data.content or ""),
            self._current_user_is_interruption,
        )

        self.user_data.reset()
        self._current_user_is_interruption = False

    async def _maybe_flush_assistant(self) -> None:
        """
        Flush accumulated assistant message data if the window is valid.

        Calculates time-to-first-audio latency, registers the assistant
        message, and checks for latency peaks that exceed the threshold.
        """
        if not self.assistant_data.has_valid_window():
            return

        # Calculate VAD-based latency to first audio
        latency_ms: float | None = None
        triggering_user_msg: dict[str, Any] | None = None

        # Find the last user message that ended before this assistant response
        for msg in reversed(self.messages):
            if (
                msg.get("role") == "user"
                and msg.get("end") is not None
                and msg["end"] <= self.assistant_data.start
            ):
                triggering_user_msg = msg
                break

        if triggering_user_msg:
            last_user_end_vad = triggering_user_msg["end"]
            # Compensate for VAD stop delay to get true user speech end
            real_end = last_user_end_vad - (self.vad_stop_secs or 0.0)
            latency_ms = (self.assistant_data.start - real_end) * 1000
            self.assistant_data.latency.vad = (self.vad_stop_secs or 0.0) * 1000

        assistant_msg = AssistantMessage(
            content=self.assistant_data.content,
            time_to_first_audio=latency_ms,
            seconds_from_start=self.assistant_data.start,
            latency=self.assistant_data.latency.get_metrics(),
        )
        self.messages.append(self.assistant_data.get_metrics())
        await self.call.register_message(assistant_msg)
        self._last_assistant_message_id = assistant_msg.id

        # Check for latency peak issue
        if (
            latency_ms is not None
            and self.latency_threshold_ms is not None
            and latency_ms > self.latency_threshold_ms
        ):
            err = IssueMessage(
                content=(
                    f"Latency peak detected: {latency_ms:.2f}ms exceeds "
                    f"threshold of {self.latency_threshold_ms}ms"
                ),
                source="observer",
                message_id=assistant_msg.id,
                seconds_from_start=self.assistant_data.start,
                code="latency_peak",
                metadata={
                    "latency_ms": latency_ms,
                    "threshold_ms": self.latency_threshold_ms,
                    "assistant_start": self.assistant_data.start,
                    "triggering_user_end": (
                        triggering_user_msg.get("end") if triggering_user_msg else None
                    ),
                    "latency_breakdown": self.assistant_data.latency.get_metrics(),
                },
            )

            logger.warning(
                "Latency peak | latency_ms=%.2f | threshold_ms=%.2f",
                latency_ms,
                self.latency_threshold_ms,
            )

            try:
                task = asyncio.create_task(self.call.register_issue(err))
                self._pending_issue_tasks.append(task)
            except Exception:
                pass

        logger.debug(
            "Assistant message flushed | chars=%d | latency_ms=%s",
            len(self.assistant_data.content or ""),
            f"{latency_ms:.2f}" if latency_ms else "N/A",
        )

        self.assistant_data.reset()

    # -----------------------------------------------------------------------
    # Schema Extraction
    # -----------------------------------------------------------------------

    async def _extract_tool_schemas(
        self,
        frame: Any,
        src: Any,
        direction: FrameDirection,
    ) -> None:
        """
        Extract and register tool schemas from the LLM service.

        Searches the processor chain for an LLM service and extracts
        function schemas from its registered tools. Only runs on
        LLMFullResponseStartFrame to avoid repeated extraction.

        Args:
            frame: The Pipecat frame being processed.
            src: The frame source processor.
            direction: Frame propagation direction.
        """
        if not (
            isinstance(frame, LLMFullResponseStartFrame)
            and is_downstream_output(src, direction)
        ):
            return

        upstream_nodes = trace_upstream(src)

        llm_service: LLMService | None = None
        for node in upstream_nodes:
            if "switcher" in node.__class__.__name__.lower():
                try:
                    strategy = getattr(node, "strategy", None)
                    if strategy:
                        active_service = getattr(strategy, "active_service", None)
                        if isinstance(active_service, LLMService):
                            llm_service = active_service
                            break
                except Exception:
                    continue
            elif isinstance(node, LLMService):
                llm_service = node
                break

        if not llm_service:
            return

        functions_dict = getattr(llm_service, "_functions", None)
        if not isinstance(functions_dict, dict):
            return

        tool_schemas: list[dict[str, Any]] = []
        for func_name, registry_item in functions_dict.items():
            try:
                schema_obj = _extract_schema_from_entry(registry_item)
                if not schema_obj:
                    continue

                schema_json = _schema_to_json(schema_obj)
                if not isinstance(schema_json, dict):
                    continue

                # Extract underscore-prefixed properties and remove the prefix
                cleaned_schema: dict[str, Any] = {}
                for key, value in schema_json.items():
                    if key.startswith("_"):
                        cleaned_key = key[1:]
                        cleaned_schema[cleaned_key] = value

                if "name" not in cleaned_schema:
                    cleaned_schema["name"] = func_name

                if cleaned_schema:
                    tool_schemas.append(cleaned_schema)
            except Exception:
                continue

        if tool_schemas:
            logger.info("Tool schemas extracted | count=%d", len(tool_schemas))
            await self.call.register_tool_schemas(tool_schemas)

    async def _extract_system_prompts(
        self,
        frame: Any,
        src: Any,
        direction: FrameDirection,
    ) -> None:
        """
        Extract and register system prompts from context aggregators.

        Searches the processor chain for context aggregator nodes and
        extracts system role messages from their message lists.

        Args:
            frame: The Pipecat frame being processed.
            src: The frame source processor.
            direction: Frame propagation direction.
        """
        if not (
            isinstance(frame, LLMFullResponseStartFrame)
            and is_downstream_output(src, direction)
        ):
            return

        upstream_nodes = trace_upstream(src)

        for node in upstream_nodes:
            if "contextaggregator" in node.__class__.__name__.lower():
                logger.debug(
                    "Context aggregator found | class=%s",
                    node.__class__.__name__,
                )

                messages_attr = getattr(node, "messages", None)
                if isinstance(messages_attr, list):
                    for msg in messages_attr:
                        if isinstance(msg, dict) and msg.get("role") == "system":
                            content = msg.get("content", "")
                            if content and isinstance(content, str):
                                preview = (
                                    content[:50] + "..."
                                    if len(content) > 50
                                    else content
                                )
                                logger.debug(
                                    "System prompt found | len=%d | preview=%s",
                                    len(content),
                                    preview,
                                )

                                await self.call.register_system_prompts(content)

    # -----------------------------------------------------------------------
    # Overlap Tracking
    # -----------------------------------------------------------------------

    def _start_overlap(self, start_t: float, interrupter: str) -> None:
        """
        Begin tracking a speech overlap period.

        Called when both user and bot are speaking simultaneously.
        Overlaps are used to detect interruption loops.

        Args:
            start_t: Overlap start timestamp (seconds from call start).
            interrupter: Who initiated the overlap ("user" or "bot").
        """
        self._overlap_active = True
        self._overlap_start_ts = start_t
        self._overlap_user_words = 0
        self._overlap_bot_words = 0
        self._overlap_interrupter = interrupter
        self._overlap_first_transcript_at = None

    def _end_overlap(self, end_t: float) -> None:
        """
        End tracking of a speech overlap period.

        Records the overlap summary for later interruption loop detection.

        Args:
            end_t: Overlap end timestamp (seconds from call start).
        """
        if self._overlap_active and self._overlap_start_ts is not None:
            interrupter = self._overlap_interrupter
            interrupter_words = 0
            if interrupter == "user":
                interrupter_words = self._overlap_user_words
            elif interrupter == "bot":
                interrupter_words = self._overlap_bot_words

            overlap_record: dict[str, Any] = {
                "start": self._overlap_start_ts,
                "first_transcript_at": self._overlap_first_transcript_at,
                "interrupter": interrupter,
                "interrupter_words": interrupter_words,
                "end": end_t,
            }

            try:
                self._overlaps_summary.append(overlap_record)
            except Exception as e:
                logger.error("Failed to record overlap | error=%s", e)

        # Reset overlap state
        self._overlap_active = False
        self._overlap_start_ts = None
        self._overlap_user_words = 0
        self._overlap_bot_words = 0
        self._overlap_interrupter = None
        self._overlap_first_transcript_at = None

    # -----------------------------------------------------------------------
    # Main Frame Handler
    # -----------------------------------------------------------------------

    async def on_push_frame(self, data: FramePushed) -> None:
        """
        Main entry point for frame event handling.

        Called by Pipecat for each frame pushed through the pipeline.
        Delegates to the implementation method with error handling.

        Args:
            data: The FramePushed event containing frame, source,
                direction, and timestamp.
        """
        if self._initialization_failed or not self._initialized:
            return

        try:
            await self._on_push_frame_impl(data)
        except Exception as e:
            logger.error(
                "Frame processing error (frame skipped) | error_type=%s | error=%s",
                type(e).__name__,
                e,
                exc_info=True,
            )

    async def _on_push_frame_impl(self, data: FramePushed) -> None:
        """
        Implementation of frame event handling logic.

        Processes each frame through the various handlers for:
        - Service timeline updates (provider/model tracking)
        - Latency metric tracking
        - Speaking window management
        - Tool call lifecycle
        - Content accumulation
        - Message flushing
        - Error frame capture
        - System prompt/tool schema extraction
        - Call finalization

        Args:
            data: The FramePushed event from Pipecat.
        """
        src = data.source
        frame = data.frame
        direction = data.direction
        t = ns_to_s(data.timestamp)

        # Update service timelines (STT/LLM/TTS provider/model tracking)
        await self._update_service_timeline(frame, src, direction, t)

        # Track latency anchor points
        self._handle_latency_markers(frame, src, direction, t)

        # Manage speaking windows
        self._handle_bot_window(frame, src, direction, t)
        self._handle_user_window(frame, src, direction, t)

        # Handle tool call lifecycle
        await self._handle_tool_call_start(frame, src, direction, t)
        await self._handle_tool_call_end(frame, src, direction, t)

        # Accumulate message content
        self._accumulate_content(frame, src, direction, t)

        # Flush completed messages
        await self._maybe_flush_user()
        await self._maybe_flush_assistant()

        # Record issues from error frames
        if isinstance(frame, ErrorFrame):
            current_issue = snapshot_error_frame(frame, ns_to_s(data.timestamp))

            logger.debug(
                "Error frame captured | error_type=%s",
                type(frame).__name__,
            )

            await self.call.register_issue(current_issue)

        # Extract system prompts and tool schemas from LLM-related frames
        await self._extract_system_prompts(frame, src, direction)
        await self._extract_tool_schemas(frame, src, direction)

        # Handle call termination (ensure finalization runs exactly once)
        if isinstance(frame, (CancelFrame, EndFrame)) and not self.final:
            if self._active_interrupt:
                self._finalize_interrupt_attempt(t, "call_ending")

            if self._overlap_active:
                self._end_overlap(t)

            # Detect interruption loops from collected overlap data
            loops: list[dict[str, Any]] = []
            try:
                loops = detect_interruption_loops(overlaps=self._overlaps_summary)
            except Exception as exc:
                logger.error("Interruption loop detection failed | error=%s", exc)

            for loop in loops:
                try:
                    loop_start = loop.get("start") or 0
                    loop_err = IssueMessage(
                        content="Interruption loop (series of interruptions at short intervals)",
                        source="observer",
                        seconds_from_start=loop_start,
                        code="interruption_loop",
                        metadata=loop,
                    )
                    task = asyncio.create_task(self.call.register_issue(loop_err))
                    self._pending_issue_tasks.append(task)
                except Exception as exc:
                    logger.error(
                        "Failed to register interruption loop issue | error=%s", exc
                    )

            self.final = True

            # Await all pending issue registration tasks
            if self._pending_issue_tasks:
                await asyncio.gather(*self._pending_issue_tasks, return_exceptions=True)

            await self.post_process_data()

    async def post_process_data(self) -> None:
        """
        Process and send call data after the call ends.

        Subclasses should override this method to collect provider-specific
        data (recording URL, duration, etc.) and call self.call.init_post_call_data().

        The base implementation is a no-op; subclasses must provide the
        actual post-call data collection logic.
        """
