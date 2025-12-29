"""
Call session management for the Connexity SDK.

This module provides the CallSession class which tracks all data and events
during a voice call session including messages, issues, and service usage.
"""

import asyncio
import datetime
from typing import Literal

from connexity.calls.messages.base_message import BaseMessage
from connexity.calls.messages.issue_message import IssueMessage
from connexity.calls.models import CallSessionData, ServiceSegment
from connexity.utils.connexity_api import send_to_gateway
from connexity.utils.logging_config import get_logger

logger = get_logger(__name__)


class CallSession:
    """
    Manages data collection and state for a single call session.

    This class tracks all relevant call data including conversation messages,
    issues, system prompts, tool schemas, and service usage timeline.

    Attributes:
        call: Reference to the CallSession instance (set during initialization)
    """

    def __init__(
        self,
        sid: str,
        call_type: Literal["inbound", "outbound", "web"],
        api_key: str,
        agent_id: str,
        user_phone_number: str | None = None,
        agent_phone_number: str | None = None,
        created_at=None,
        voice_engine: str | None = None,
        phone_call_provider: str | None = None,
        run_mode: Literal["production", "development"] | None = "development",
        vad_analyzer: str | None = None,
    ):
        """
        Initialize a new CallSession.

        Args:
            sid: Unique session identifier
            call_type: Type of call ("inbound", "outbound", or "web")
            api_key: Connexity API key for authentication
            agent_id: Identifier for the AI agent
            user_phone_number: The user's phone number (optional)
            agent_phone_number: The agent's phone number (optional)
            created_at: Call creation timestamp (optional)
            voice_engine: Voice processing engine identifier
            phone_call_provider: Telephony provider name
            run_mode: Environment mode ("production" or "development")
            vad_analyzer: Voice Activity Detection analyzer name
        """
        # Core identifiers
        self._sid = sid
        self._call_type = call_type
        self._agent_id = agent_id
        self._api_key = api_key

        # Phone configuration
        self._user_phone_number = user_phone_number
        self._agent_phone_number = agent_phone_number
        self._phone_call_provider = phone_call_provider

        # Call metadata
        self._created_at = created_at
        self._voice_engine = voice_engine
        self._run_mode = run_mode
        self._vad_analyzer = vad_analyzer

        # Current service providers/models (updated via timeline)
        self._stt_provider = None
        self._stt_model = None
        self._tts_provider = None
        self._tts_model = None
        self._tts_voice = None
        self._llm_provider = None
        self._llm_model = None

        # Post-call data
        self._duration_in_seconds = None
        self._recording_url = None

        # Conversation data
        self._system_prompts: set[str] = set()
        self._tool_schemas: list[dict] = []
        self._registered_tool_names: set[str] = set()
        self._messages: list[BaseMessage] = []
        self._issues: list[IssueMessage] = []
        self._issues_registered: set[str] = set()

        # Service usage timeline
        self._services_timeline: dict[str, list[ServiceSegment]] = {
            "stt": [],
            "llm": [],
            "tts": [],
        }

    async def initialize(self):
        """Async method to handle post-init operations."""

    async def register_message(self, message: BaseMessage):
        """
        Register a new conversation message.

        Args:
            message: The message to add to the conversation history
        """
        self._messages.append(message)

    async def register_issue(self, issue: IssueMessage):
        """
        Register an issue that occurred during the call.

        Duplicate issues (by ID) are ignored to prevent redundant logging.

        Args:
            issue: The issue to register
        """
        if issue.id and issue.id not in self._issues_registered:
            self._issues.append(issue)
            self._issues_registered.add(issue.id)

    async def update_last_message(self, message: BaseMessage):
        """
        Update the most recent message in the conversation.

        Args:
            message: The updated message content
        """
        self._messages[-1] = message

    async def register_system_prompts(self, prompts: set[str]):
        """
        Register system prompts used in the conversation.

        Args:
            prompts: Set of system prompt strings
        """
        self._system_prompts.add(prompts)

    async def register_tool_schemas(self, schemas: list[dict]):
        """
        Register tool schemas available to the agent.

        Duplicate tools (by name) are ignored.

        Args:
            schemas: List of tool schema dictionaries
        """
        for schema in schemas:
            tool_name = schema.get("name")
            if tool_name and tool_name not in self._registered_tool_names:
                self._registered_tool_names.add(tool_name)
                self._tool_schemas.append(schema)

    async def init_post_call_data(
        self,
        recording_url: str,
        duration_in_seconds: float,
        created_at: datetime.datetime | None,
    ):
        """
        Initialize post-call data and send to Connexity backend.

        This method should be called after the call ends to finalize
        the session data and transmit it for processing.

        Args:
            recording_url: URL to the call recording
            duration_in_seconds: Total call duration
            created_at: Call creation timestamp
        """
        self._recording_url = recording_url
        self._duration_in_seconds = duration_in_seconds
        self._created_at = created_at

        self.finalize_services_timeline(self._duration_in_seconds)

        await self._send_data_to_connexity()

    def _to_dict(self) -> CallSessionData:
        """
        Convert the CallSession to a Pydantic model representation.

        Returns:
            CallSessionData: Pydantic model containing all call session data
        """
        return CallSessionData(
            sid=self._sid,
            call_type=self._call_type,
            user_phone_number=self._user_phone_number,
            agent_phone_number=self._agent_phone_number,
            created_at=self._created_at.isoformat()
            if hasattr(self._created_at, "isoformat")
            else self._created_at,
            agent_id=self._agent_id,
            voice_engine=self._voice_engine,
            stt_provider=self._stt_provider,
            stt_model=self._stt_model,
            tts_provider=self._tts_provider,
            tts_model=self._tts_model,
            tts_voice=self._tts_voice,
            llm_provider=self._llm_provider,
            llm_model=self._llm_model,
            phone_call_provider=self._phone_call_provider,
            duration_in_seconds=self._duration_in_seconds,
            recording_url=self._recording_url,
            messages=[message.to_dict() for message in self._messages]
            if self._messages
            else [],
            run_mode=self._run_mode,
            vad_analyzer=self._vad_analyzer,
            issues=[e.to_dict() for e in self._issues] if self._issues else [],
            system_prompts=sorted(self._system_prompts) if self._system_prompts else [],
            tool_schemas=self._tool_schemas if self._tool_schemas else [],
            services_timeline=self._services_timeline,
        )

    async def _send_data_to_connexity(self):
        """
        Send accumulated call data to Connexity's backend.
        """
        data = self._to_dict()
        data.event_type = "end_of_call"
        data.status = "completed"

        asyncio.create_task(send_to_gateway(data.model_dump(), self._api_key))

    # --- Services Timeline Management ---

    def _last_segment(
        self, kind: Literal["stt", "llm", "tts"]
    ) -> ServiceSegment | None:
        """
        Get the most recent segment for a service type.

        Args:
            kind: The service type ("stt", "llm", or "tts")

        Returns:
            The most recent ServiceSegment or None if no segments exist
        """
        segs = self._services_timeline.get(kind) or []
        return segs[-1] if segs else None

    async def update_service_timeline(
        self,
        kind: Literal["stt", "llm", "tts"],
        *,
        provider: str | None = None,
        model: str | None = None,
        voice: str | None = None,
        at_seconds: float | None = None,
    ):
        """
        Update the service timeline when provider/model changes.

        This method tracks service usage over time, creating new segments
        when the provider, model, or voice changes.

        Args:
            kind: The service type ("stt", "llm", or "tts")
            provider: The service provider name
            model: The model identifier
            voice: The voice identifier (TTS only)
            at_seconds: Timestamp in seconds from call start
        """

        def norm(v: str | None) -> str:
            return (v or "").strip().lower()

        last = self._last_segment(kind)
        changed = (
            not last
            or norm(last.provider) != norm(provider)
            or norm(last.model) != norm(model)
            or (kind == "tts" and norm(last.voice) != norm(voice))
        )

        if changed:
            # Close the previous segment
            if last and last.end is None:
                last.end = at_seconds

            # Create new segment
            self._services_timeline[kind].append(
                ServiceSegment(
                    provider=provider,
                    model=model,
                    voice=(voice if kind == "tts" else None),
                    start=at_seconds,
                )
            )

            # Update current service references
            if kind == "stt":
                self._stt_provider = provider
                self._stt_model = model
            elif kind == "llm":
                self._llm_provider = provider
                self._llm_model = model
            elif kind == "tts":
                self._tts_provider = provider
                self._tts_model = model
                self._tts_voice = voice

    def finalize_services_timeline(self, at_seconds: float | None = None):
        """
        Close all open service timeline segments.

        This should be called at the end of a call to ensure all
        segments have proper end times.

        Args:
            at_seconds: The final timestamp (typically call duration)
        """
        for segs in self._services_timeline.values():
            if segs and segs[-1].end is None:
                segs[-1].end = at_seconds
