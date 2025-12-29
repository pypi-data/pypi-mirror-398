"""
=========================================================================
SSE Client for CLI Streaming
SDLC Orchestrator - Sprint 52

Version: 1.0.0
Date: December 26, 2025
Status: ACTIVE - Sprint 52 Implementation
Authority: Backend Team + CTO Approved

Purpose:
- Consume SSE events from backend /codegen/generate/stream endpoint
- Parse streaming events and yield typed event objects
- Support resume from previous session
- Handle connection errors gracefully

References:
- docs/02-design/14-Technical-Specs/Session-Checkpoint-Design.md
- backend/app/schemas/streaming.py
=========================================================================
"""

import json
import logging
from dataclasses import dataclass
from typing import AsyncGenerator, Optional, Union

import httpx

logger = logging.getLogger(__name__)


# ============================================================================
# Event Types (matches backend streaming.py)
# ============================================================================


@dataclass
class StartedEvent:
    """Generation started event."""

    type: str = "started"
    session_id: str = ""
    model: str = ""
    provider: str = ""
    timestamp: str = ""


@dataclass
class FileGeneratingEvent:
    """File generation in progress event."""

    type: str = "file_generating"
    session_id: str = ""
    path: str = ""
    timestamp: str = ""


@dataclass
class FileGeneratedEvent:
    """File generation complete event."""

    type: str = "file_generated"
    session_id: str = ""
    path: str = ""
    content: str = ""
    lines: int = 0
    language: str = ""
    syntax_valid: bool = True
    timestamp: str = ""


@dataclass
class CheckpointEvent:
    """Checkpoint saved event."""

    type: str = "checkpoint"
    session_id: str = ""
    checkpoint_number: int = 0
    files_completed: int = 0
    total_files: int = 0
    last_file: str = ""
    timestamp: str = ""


@dataclass
class CompletedEvent:
    """Generation completed event."""

    type: str = "completed"
    session_id: str = ""
    total_files: int = 0
    total_lines: int = 0
    duration_ms: int = 0
    success: bool = True
    timestamp: str = ""


@dataclass
class ErrorEvent:
    """Error event."""

    type: str = "error"
    session_id: str = ""
    message: str = ""
    recovery_id: Optional[str] = None
    timestamp: str = ""


@dataclass
class SessionResumedEvent:
    """Session resumed event."""

    type: str = "session_resumed"
    session_id: str = ""
    resumed_from_checkpoint: int = 0
    files_already_completed: int = 0
    files_remaining: int = 0
    timestamp: str = ""


StreamEvent = Union[
    StartedEvent,
    FileGeneratingEvent,
    FileGeneratedEvent,
    CheckpointEvent,
    CompletedEvent,
    ErrorEvent,
    SessionResumedEvent,
]


# ============================================================================
# SSE Client
# ============================================================================


class SSEStreamClient:
    """
    Client for consuming SSE events from SDLC Orchestrator backend.

    Handles streaming code generation with real-time progress updates.
    """

    def __init__(
        self,
        api_url: str,
        token: Optional[str] = None,
        timeout: float = 300.0,
    ):
        """
        Initialize SSE client.

        Args:
            api_url: Base URL of the API (e.g., http://localhost:8320/api/v1)
            token: Optional JWT token for authentication
            timeout: Request timeout in seconds (default 5 minutes for long generations)
        """
        self.api_url = api_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def _get_headers(self) -> dict[str, str]:
        """Build request headers."""
        headers = {
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _parse_event(self, event_data: str) -> Optional[StreamEvent]:
        """
        Parse SSE event data into typed event object.

        Args:
            event_data: JSON string from SSE data field

        Returns:
            Typed event object or None if parsing fails
        """
        try:
            data = json.loads(event_data)
            event_type = data.get("type", "")

            if event_type == "started":
                return StartedEvent(
                    type="started",
                    session_id=data.get("session_id", ""),
                    model=data.get("model", ""),
                    provider=data.get("provider", ""),
                    timestamp=data.get("timestamp", ""),
                )
            elif event_type == "file_generating":
                return FileGeneratingEvent(
                    type="file_generating",
                    session_id=data.get("session_id", ""),
                    path=data.get("path", ""),
                    timestamp=data.get("timestamp", ""),
                )
            elif event_type == "file_generated":
                return FileGeneratedEvent(
                    type="file_generated",
                    session_id=data.get("session_id", ""),
                    path=data.get("path", ""),
                    content=data.get("content", ""),
                    lines=data.get("lines", 0),
                    language=data.get("language", ""),
                    syntax_valid=data.get("syntax_valid", True),
                    timestamp=data.get("timestamp", ""),
                )
            elif event_type == "checkpoint":
                return CheckpointEvent(
                    type="checkpoint",
                    session_id=data.get("session_id", ""),
                    checkpoint_number=data.get("checkpoint_number", 0),
                    files_completed=data.get("files_completed", 0),
                    total_files=data.get("total_files", 0),
                    last_file=data.get("last_file", ""),
                    timestamp=data.get("timestamp", ""),
                )
            elif event_type == "completed":
                return CompletedEvent(
                    type="completed",
                    session_id=data.get("session_id", ""),
                    total_files=data.get("total_files", 0),
                    total_lines=data.get("total_lines", 0),
                    duration_ms=data.get("duration_ms", 0),
                    success=data.get("success", True),
                    timestamp=data.get("timestamp", ""),
                )
            elif event_type == "error":
                return ErrorEvent(
                    type="error",
                    session_id=data.get("session_id", ""),
                    message=data.get("message", "Unknown error"),
                    recovery_id=data.get("recovery_id"),
                    timestamp=data.get("timestamp", ""),
                )
            elif event_type == "session_resumed":
                return SessionResumedEvent(
                    type="session_resumed",
                    session_id=data.get("session_id", ""),
                    resumed_from_checkpoint=data.get("resumed_from_checkpoint", 0),
                    files_already_completed=data.get("files_already_completed", 0),
                    files_remaining=data.get("files_remaining", 0),
                    timestamp=data.get("timestamp", ""),
                )
            else:
                logger.warning(f"Unknown event type: {event_type}")
                return None

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse SSE event: {e}")
            return None

    async def stream_generate(
        self,
        blueprint: dict,
        session_id: Optional[str] = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Stream code generation events from backend.

        Args:
            blueprint: AppBlueprint dictionary
            session_id: Optional session ID to resume from

        Yields:
            StreamEvent objects as they are received

        Raises:
            httpx.HTTPError: On connection errors
            httpx.TimeoutException: On request timeout
        """
        # Determine endpoint
        if session_id:
            endpoint = f"{self.api_url}/codegen/generate/resume/{session_id}"
            method = "POST"
            body: Optional[dict] = None
        else:
            endpoint = f"{self.api_url}/codegen/generate/stream"
            method = "POST"
            body = {"app_blueprint": blueprint}

        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                method,
                endpoint,
                json=body,
                headers=headers,
            ) as response:
                # Check for errors
                if response.status_code >= 400:
                    error_text = await response.aread()
                    raise httpx.HTTPStatusError(
                        f"HTTP {response.status_code}: {error_text.decode()}",
                        request=response.request,
                        response=response,
                    )

                # Parse SSE stream
                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk

                    # Process complete events (separated by \n\n)
                    while "\n\n" in buffer:
                        event_str, buffer = buffer.split("\n\n", 1)

                        # Parse data field
                        for line in event_str.split("\n"):
                            if line.startswith("data: "):
                                data = line[6:].strip()
                                if data:
                                    event = self._parse_event(data)
                                    if event:
                                        yield event

    async def check_health(self) -> bool:
        """
        Check if the backend is healthy.

        Returns:
            True if backend is healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.api_url}/health")
                return response.status_code == 200
        except Exception:
            return False
