"""
PLANQK Session Runtime Client

This module provides a wrapper that bridges IBM Qiskit Runtime Session API calls
to PLANQK client session methods. It focuses specifically on session management
functionality to enable seamless integration with IBM's Session class.
"""

from typing import Optional, Dict, Any

from planqk.quantum.sdk.client.client import _PlanqkClient
from planqk.quantum.sdk.client.model_enums import Provider, PlanqkSdkProvider
from planqk.quantum.sdk.client.session_dtos import SessionStatus, SessionMode


class RuntimeSessionClientAdapter:
    """Session Runtime Client wrapper for PLANQK integration.

    This class provides a compatibility layer between IBM Qiskit Runtime Session API
    and PLANQK's session management infrastructure. It translates IBM API calls into
    PLANQK client calls and converts responses back to IBM-expected formats.

    The wrapper focuses exclusively on session-related functionality:
    - Creating sessions
    - Retrieving session details
    - Closing sessions

    This enables the standard IBM Session class to work transparently with PLANQK backends.
    """

    def __init__(self, planqk_client: _PlanqkClient):
        """Initialize the session runtime client wrapper.

        Args:
            planqk_client: The PLANQK client instance to wrap for session operations.
        """
        self._planqk_client = planqk_client

    @staticmethod
    def _convert_usage_time_to_seconds(usage_time_millis: Optional[int]) -> Optional[float]:
        return usage_time_millis / 1000.0 if usage_time_millis is not None else None

    def create_session(self, backend,
                       instance: Optional[str] = None,
                       max_time: Optional[int] = None,
                       channel: Optional[str] = None,
                       session_mode: Optional[str] = None,
                       **kwargs) -> Dict[str, Any]:
        """Create a session using IBM Qiskit Runtime API format.

        This method translates IBM Session creation requests into PLANQK client calls,
        handling parameter mapping and response format conversion.

        Args:
            backend: Backend object or backend name
            instance: IBM Cloud instance identifier (ignored - not supported in PLANQK)
            max_time: Maximum session time in seconds (mapped to TTL parameter)
            channel: IBM communication channel (ignored - PLANQK handles routing)
            session_mode: Session mode (ignored - uses DEDICATED for PLANQK)
            **kwargs: Additional session parameters (e.g., metadata)

        Returns:
            Dict with session information in IBM API format

        Raises:
            PlanqkClientError: If session creation fails
            InvalidAccessTokenError: If authentication fails
        """

        # Extract backend name from backend object or use as-is if string
        backend_name = backend.name if hasattr(backend, 'name') else str(backend)

        # Convert session mode string to enum
        if session_mode == "dedicated":
            mode = SessionMode.DEDICATED
        elif session_mode == "batch":
            mode = SessionMode.BATCH
        elif session_mode is None:
            mode = SessionMode.DEDICATED
        else:
            raise ValueError(f"Invalid session mode: {session_mode}. Must be 'dedicated' or 'batch'")

        # Create session via PLANQK client (use backend name as-is)
        session_response = self._planqk_client.create_session(
            backend_id=backend_name,
            provider=Provider.IBM,
            mode=mode,
            ttl=max_time,
            metadata=kwargs.get('metadata'),
            sdk_provider=PlanqkSdkProvider.QISKIT
        )

        # Convert to IBM API format
        return {
            'id': session_response.id,
            'backend_name': backend_name,
            'state': self._convert_status_to_ibm(session_response.status),
            'mode': session_response.mode.value,
            'created_at': session_response.created_at
        }


    def session_details(self, session_id: str) -> Dict[str, Any]:
        """Get session details using IBM Qiskit Runtime API format.

        This method retrieves session information from PLANQK and converts it to
        IBM API format with all required fields.

        Args:
            session_id: The session identifier

        Returns:
            Dict with detailed session information in IBM API format.

        Raises:
            PlanqkClientError: If session retrieval fails
            InvalidAccessTokenError: If authentication fails
        """

        session_response = self._planqk_client.get_session(session_id)

        # Helper function to safely access metadata
        def get_metadata(key: str):
            return session_response.metadata.get(key) if session_response.metadata else None

        usage_time_seconds = self._convert_usage_time_to_seconds(session_response.usage_time_millis)

        return {
            "id": session_response.id,
            "ibm_id": session_response.provider_id,
            "backend_name": session_response.backend_id,
            "max_ttl": get_metadata("max_ttl"),
            "active_ttl": get_metadata("active_ttl"),
            "interactive_ttl": get_metadata("interactive_ttl"),
            "state": self._convert_status_to_ibm(session_response.status),
            "accepting_jobs": session_response.status not in {SessionStatus.CLOSED, SessionStatus.UNKNOWN, SessionStatus.DRAINING},
            "last_job_started": get_metadata("last_job_started"),
            "last_job_completed": get_metadata("last_job_completed"),
            "started_at": session_response.created_at,
            "closed_at": session_response.closed_at,
            "activated_at": session_response.started_at,
            "mode": session_response.mode.value,
            "elapsed_time": usage_time_seconds
        }

    def close_session(self, session_id: str) -> None:
        """Close a session using IBM Qiskit Runtime API format.

        This method closes a session by delegating directly to the PLANQK client.
        The operation is idempotent and matches IBM's session closure behavior.

        Args:
            session_id: The session identifier

        Raises:
            PlanqkClientError: If session closure fails
            InvalidAccessTokenError: If authentication fails
        """
        self._planqk_client.close_session(session_id)

    def cancel_session(self, session_id: str) -> None:
        """Cancel a session using IBM Qiskit Runtime API format.

        This method cancels a session by delegating directly to the PLANQK client.
        Unlike close_session, cancel_session terminates the session immediately
        and cancels any running or queued jobs within the session.

        Args:
            session_id: The session identifier

        Raises:
            PlanqkClientError: If session cancellation fails
            InvalidAccessTokenError: If authentication fails
        """
        self._planqk_client.cancel_session(session_id)

    def _convert_status_to_ibm(self, planqk_status: SessionStatus) -> str:
        """Convert PLANQK session status to IBM format.

        This method maps PLANQK SessionStatus enum values to IBM string format
        as expected by the IBM Session API.

        Args:
            planqk_status: PLANQK SessionStatus enum value

        Returns:
            IBM status string ('open', 'active', 'inactive', 'closed', etc.)
        """
        status_mapping = {
            SessionStatus.OPEN: 'open',
            SessionStatus.ACTIVE: 'active',
            SessionStatus.INACTIVE: 'inactive',
            SessionStatus.CLOSED: 'closed',
            SessionStatus.DRAINING: 'active',
        }
        fallback_status = planqk_status.value.upper()
        return status_mapping.get(planqk_status, fallback_status)
