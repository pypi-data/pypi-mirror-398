from enum import Enum
from typing import Optional, Dict

from pydantic import BaseModel, field_validator

from planqk.quantum.sdk.client.model_enums import Provider, PlanqkSdkProvider


class SessionMode(Enum):
    """Session execution mode enum."""
    BATCH = "batch"
    DEDICATED = "dedicated"


class SessionStatus(Enum):
    """Session status enum matching PLANQK API."""
    UNKNOWN = "UNKNOWN"
    ABORTED = "ABORTED"
    OPEN = "OPEN"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DRAINING = "DRAINING"
    CLOSED = "CLOSED"


class CreateSessionRequest(BaseModel):
    """Request model for session creation matching PLANQK API."""
    backend_id: str
    provider: Provider
    mode: SessionMode
    ttl: Optional[int] = None
    metadata: Optional[Dict] = None
    sdk_provider: Optional[PlanqkSdkProvider] = PlanqkSdkProvider.QISKIT

    @field_validator('provider', mode='before')
    def _validate_provider(cls, v):
        """Validate and convert provider to enum."""
        if v is None:
            return Provider.UNKNOWN

        if isinstance(v, str):
            try:
                return Provider[v.upper()]
            except KeyError:
                return Provider.UNKNOWN

        return v

    @field_validator('mode', mode='before')
    def _validate_mode(cls, v):
        """Validate and convert mode to enum."""
        if isinstance(v, str):
            try:
                return SessionMode(v.lower())
            except ValueError:
                return SessionMode.DEDICATED  # Default fallback

        return v

    @field_validator('sdk_provider', mode='before')
    def _validate_sdk_provider(cls, v):
        """Validate and convert sdk_provider to enum."""
        if v is None:
            return PlanqkSdkProvider.QISKIT  # Default for sessions

        if isinstance(v, str):
            try:
                return PlanqkSdkProvider[v.upper()]
            except KeyError:
                return PlanqkSdkProvider.QISKIT

        return v

    def model_dump(self, **kwargs) -> dict:
        """Convert to dict with proper serialization for API."""
        data = super().model_dump(**kwargs)

        # Convert enums to their string values for API
        if 'provider' in data and hasattr(data['provider'], 'name'):
            data['provider'] = data['provider'].name
        if 'mode' in data and hasattr(data['mode'], 'value'):
            data['mode'] = data['mode'].value
        if 'sdk_provider' in data and hasattr(data['sdk_provider'], 'value'):
            data['sdk_provider'] = data['sdk_provider'].value

        return data


class SessionResponse(BaseModel):
    """Response model for session data matching PLANQK API."""
    id: str
    backend_id: str
    provider: Provider
    status: SessionStatus
    mode: SessionMode
    created_at: str
    started_at: Optional[str] = None
    closed_at: Optional[str] = None
    expires_at: Optional[str] = None
    usage_time_millis: Optional[int] = None
    provider_id: Optional[str] = None
    metadata: Optional[Dict] = None
    sdk_provider: Optional[PlanqkSdkProvider] = None

    @field_validator('provider', mode='before')
    def _validate_provider(cls, v):
        """Validate and convert provider to enum."""
        if v is None:
            return Provider.UNKNOWN

        if isinstance(v, str):
            try:
                return Provider[v.upper()]
            except KeyError:
                return Provider.UNKNOWN

        return v

    @field_validator('status', mode='before')
    def _validate_status(cls, v):
        """Validate and convert status to enum."""
        if isinstance(v, str):
            try:
                return SessionStatus(v.upper())
            except ValueError:
                return SessionStatus.UNKNOWN  # Default fallback for unknown status

        return v

    @field_validator('mode', mode='before')
    def _validate_mode(cls, v):
        """Validate and convert mode to enum."""
        if isinstance(v, str):
            try:
                return SessionMode(v.lower())
            except ValueError:
                return SessionMode.DEDICATED  # Default fallback

        return v

    @field_validator('sdk_provider', mode='before')
    def _validate_sdk_provider(cls, v):
        """Validate and convert sdk_provider to enum."""
        if v is None:
            return None  # Allow None for backwards compatibility

        if isinstance(v, str):
            try:
                return PlanqkSdkProvider[v.upper()]
            except KeyError:
                return None  # Return None if invalid value

        return v

    def is_final(self) -> bool:
        """Check if session is in a final state."""
        final_states = {SessionStatus.CLOSED, SessionStatus.EXPIRED, SessionStatus.FAILED}
        return self.status in final_states

    def can_submit_jobs(self) -> bool:
        """Check if session can accept new job submissions."""
        accepting_states = {SessionStatus.ACTIVE, SessionStatus.INACTIVE, SessionStatus.OPEN}
        return self.status in accepting_states

    def has_backend(self, backend_id: str) -> bool:
        """Check if session belongs to a specific backend."""
        return self.backend_id == backend_id