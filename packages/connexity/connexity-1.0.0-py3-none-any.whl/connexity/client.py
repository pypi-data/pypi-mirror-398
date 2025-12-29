"""
Connexity SDK client for call session management.

This module provides the main entry point for creating and managing
call sessions with the Connexity observability platform.
"""

from typing import Literal

from connexity.calls.call_session import CallSession


class ConnexityClient:
    """
    Main SDK client for creating and managing Connexity call sessions.

    This client handles authentication and provides methods to register
    new call sessions for observability tracking.

    Example:
        client = ConnexityClient(api_key="your-api-key")
        call = await client.register_call(
            sid="call-123",
            agent_id="agent-456",
            call_type="inbound",
        )
    """

    def __init__(self, api_key: str):
        """
        Initialize the Connexity client.

        Args:
            api_key: Your Connexity API key for authentication

        Raises:
            ValueError: If api_key is empty or None
        """
        if not api_key:
            raise ValueError("API key is required")
        self.api_key = api_key

    async def register_call(
        self,
        sid: str,
        agent_id: str,
        call_type: Literal["inbound", "outbound", "web"],
        user_phone_number: str | None = None,
        agent_phone_number: str | None = None,
        created_at=None,
        voice_engine: str | None = None,
        phone_call_provider: str | None = None,
        run_mode: Literal["production", "development"] | None = "development",
        vad_analyzer: str | None = None,
    ) -> CallSession:
        """
        Register a new call session for observability tracking.

        Args:
            sid: Unique session identifier for the call
            agent_id: Identifier for the AI agent handling the call
            call_type: Type of call - "inbound", "outbound", or "web"
            user_phone_number: The caller's phone number (optional)
            agent_phone_number: The agent's phone number (optional)
            created_at: Call creation timestamp (optional)
            voice_engine: Voice processing engine identifier (optional)
            phone_call_provider: Telephony provider name (optional)
            run_mode: Environment mode - "production" or "development" (default)
            vad_analyzer: Voice Activity Detection analyzer name (optional)

        Returns:
            CallSession: An initialized call session ready for event tracking
        """
        call = CallSession(
            sid=sid,
            call_type=call_type,
            user_phone_number=user_phone_number,
            agent_phone_number=agent_phone_number,
            created_at=created_at,
            agent_id=agent_id,
            api_key=self.api_key,
            voice_engine=voice_engine,
            phone_call_provider=phone_call_provider,
            run_mode=run_mode,
            vad_analyzer=vad_analyzer,
        )
        await call.initialize()
        return call
