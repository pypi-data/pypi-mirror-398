"""
Data models for Connexity call sessions.

This module defines the Pydantic models used for representing call session data
and service timeline segments.

Terminology standardization:
    - STT (Speech-to-Text): stt_provider, stt_model
    - TTS (Text-to-Speech): tts_provider, tts_model, tts_voice
    - LLM (Large Language Model): llm_provider, llm_model
"""

from typing import Any, Literal

from pydantic import BaseModel

from connexity import __version__


class ServiceSegment(BaseModel):
    """
    Represents a segment of service usage during a call.

    A service segment tracks when a specific provider/model combination
    was active during a call session.

    Attributes:
        provider: The service provider (e.g., "deepgram", "openai", "elevenlabs")
        model: The specific model used (e.g., "nova-2", "gpt-4", "eleven_monolingual_v1")
        voice: The voice ID (only applicable for TTS segments)
        start: Start time in seconds from call beginning
        end: End time in seconds from call beginning
    """

    provider: str | None = None
    model: str | None = None
    voice: str | None = None
    start: float | None = None
    end: float | None = None


class CallSessionData(BaseModel):
    """
    Complete data model for a call session.

    This model contains all information about a call session including
    configuration, messages, issues, and service usage timeline.

    Attributes:
        sid: Unique session identifier
        call_type: Type of call ("inbound", "outbound", or "web")
        user_phone_number: The user's phone number (if applicable)
        agent_phone_number: The agent's phone number (if applicable)
        created_at: ISO format timestamp of call creation
        agent_id: Identifier for the AI agent
        voice_engine: The voice processing engine used
        stt_provider: Speech-to-Text service provider
        stt_model: Speech-to-Text model identifier
        tts_provider: Text-to-Speech service provider
        tts_model: Text-to-Speech model identifier
        tts_voice: Text-to-Speech voice identifier
        llm_provider: Large Language Model service provider
        llm_model: Large Language Model identifier
        phone_call_provider: Telephony provider (e.g., "twilio", "daily")
        duration_in_seconds: Total call duration
        recording_url: URL to the call recording
        messages: List of conversation messages
        run_mode: Environment mode ("production" or "development")
        vad_analyzer: Voice Activity Detection analyzer used
        issues: List of issues encountered during the call
        system_prompts: List of system prompts used
        tool_schemas: List of tool schemas available to the agent
        services_timeline: Timeline of service usage during the call
        event_type: Type of event (e.g., "end_of_call")
        status: Call status (e.g., "completed")
        sdk_version: Version of the connexity SDK
    """

    sid: str
    call_type: Literal["inbound", "outbound", "web"]
    user_phone_number: str | None = None
    agent_phone_number: str | None = None
    created_at: str | None = None
    agent_id: str
    voice_engine: str | None = None
    stt_provider: str | None = None
    stt_model: str | None = None
    tts_provider: str | None = None
    tts_model: str | None = None
    tts_voice: str | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    phone_call_provider: str | None = None
    duration_in_seconds: float | None = None
    recording_url: str | None = None
    messages: list[dict[str, Any]] = []
    run_mode: Literal["production", "development"] | None = None
    vad_analyzer: str | None = None
    issues: list[dict[str, Any]] = []
    system_prompts: list[str] = []
    tool_schemas: list[dict[str, Any]] = []
    services_timeline: dict[str, list[ServiceSegment]] = {}
    event_type: str | None = None
    status: str | None = None
    sdk_version: str = __version__
