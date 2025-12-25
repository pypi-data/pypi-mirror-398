import json
import logging
import os
import random
from typing import List, Optional, Callable, Any, Dict

import requests
from requests import Response, HTTPError

from planqk.quantum.sdk.client.backend_dtos import BackendDto, BackendStateInfosDto
from planqk.quantum.sdk.client.job_dtos import JobDto
from planqk.quantum.sdk.client.model_enums import PlanqkJobStatus
from planqk.quantum.sdk.client.session_dtos import CreateSessionRequest, SessionResponse, SessionMode
from planqk.quantum.sdk.context import ContextResolver
from planqk.quantum.sdk.credentials import DefaultCredentialsProvider
from planqk.quantum.sdk.exceptions import InvalidAccessTokenError, PlanqkClientError, PlanqkError

HEADER_CLOUD_TRACE_CTX = "x-cloud-trace-context"

logger = logging.getLogger(__name__)


def base_url():
    return os.environ.get("PLANQK_QUANTUM_BASE_URL", "https://platform.planqk.de/quantum")


def service_execution_id():
    return os.environ.get("SERVICE_EXECUTION_ID", None)


def _dict_values_to_string(obj_values_dict: dict):
    for key in obj_values_dict:
        obj_value = obj_values_dict[key]
        if not isinstance(obj_value, str):
            str_value = json.dumps(obj_value)
            obj_values_dict[key] = str_value


class _PlanqkClient:
    def __init__(self, access_token: Optional[str] = None, organization_id: Optional[str] = None):
        self._credentials = DefaultCredentialsProvider(access_token)
        self._context_resolver = ContextResolver()
        self._organization_id = organization_id

    def get_credentials(self):
        return self._credentials

    def set_organization_id(self, organization_id: str):
        self._organization_id = organization_id

    def get_organization_id(self) -> Optional[str]:
        """Get the current organization ID.
        
        Returns:
            The organization ID if set, None otherwise.
        """
        return self._organization_id

    def perform_request(self, request_func: Callable[..., Response], url: str, params=None, data=None, headers=None):
        headers = {**self._get_default_headers(), **(headers or {})}
        debug = os.environ.get("PLANQK_QUANTUM_DEBUG", "false").lower() == "true"

        trace_id = headers.get(HEADER_CLOUD_TRACE_CTX, 'unknown')
        try:
            response = request_func(url, json=data, params=params, headers=headers, verify=not debug)
            response.raise_for_status()
            return response.json() if response.status_code != 204 else None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot connect to middleware under {url} (Trace {trace_id}): {e}")
            raise e
        except HTTPError as e:
            logger.error(f"Request {request_func.__name__} {url} failed (Trace {trace_id}): {e}")
            if e.response.status_code == 401:
                raise InvalidAccessTokenError
            else:
                raise PlanqkClientError(e.response)
        except Exception as e:
            logger.error(f"Request {request_func.__name__} {url} failed (Trace {trace_id}): {e}")
            raise PlanqkError("Error while performing request") from e

    def get_backends(self) -> List[BackendDto]:
        headers = {}
        params = {"onlyPlanqkSdk": True}

        response = self.perform_request(requests.get, f"{base_url()}/backends", params=params, headers=headers)

        return [BackendDto(**backend_info) for backend_info in response]

    def get_backend(self, backend_id: str) -> BackendDto:
        headers = {}

        response = self.perform_request(requests.get, f"{base_url()}/backends/{backend_id}", headers=headers)
        return BackendDto(**response)

    def get_backend_state(self, backend_id: str) -> BackendStateInfosDto:
        headers = {}

        response = self.perform_request(requests.get, f"{base_url()}/backends/{backend_id}/status", headers=headers)
        return BackendStateInfosDto(**response)

    def get_backend_config(self, backend_id: str) -> Dict[str, Any]:
        headers = {}

        response = self.perform_request(requests.get, f"{base_url()}/backends/{backend_id}/config", headers=headers)
        return response

    def get_backend_calibration(self, backend_id: str) -> Dict[str, Any]:
        headers = {}
        response = self.perform_request(requests.get, f"{base_url()}/backends/{backend_id}/calibration", headers=headers)
        return response

    def submit_job(self, job: JobDto) -> JobDto:
        headers = {"content-type": "application/json"}

        # Create dict from job object and remove attributes with None values from it
        job_dict = self._remove_none_values(job.model_dump())

        response = self.perform_request(requests.post, f"{base_url()}/jobs", data=job_dict, headers=headers)
        return JobDto(**response)

    def get_job(self, job_id: str) -> JobDto:
        params = {}
        response = self.perform_request(requests.get, f"{base_url()}/jobs/{job_id}", params=params)
        return JobDto(**response)

    def get_jobs(self) -> List[JobDto]:
        jobs = []
        page = 0
        size = 50

        while True:
            # Request the current page of jobs
            response = self.perform_request(
                requests.get,
                f"{base_url()}/jobs",
                params={"page": page, "size": size}
            )

            # Add the jobs from the current page to the list
            jobs.extend(JobDto(**job_info) for job_info in response.get('content', []))

            # Check if the current page is the last one
            if response.get('last', True):
                break

            page += 1

        return jobs

    def get_job_status(self, job_id: str) -> PlanqkJobStatus:
        response = self.perform_request(requests.get, f"{base_url()}/jobs/{job_id}/status")
        return PlanqkJobStatus[response['status'].upper()]

    def get_job_result(self, job_id: str) -> Dict[str, Any]:
        response = self.perform_request(requests.get, f"{base_url()}/jobs/{job_id}/result")
        return response

    def get_job_calibration(self, job_id: str) -> Dict[str, Any]:
        response = self.perform_request(requests.get, f"{base_url()}/jobs/{job_id}/calibration")
        return response

    def cancel_job(self, job_id: str) -> None:
        self.perform_request(requests.delete, f"{base_url()}/jobs/{job_id}")

    def create_session(self, backend_id: str, provider, mode: SessionMode,
                      ttl: Optional[int] = None, metadata: Optional[Dict] = None,
                      sdk_provider = None) -> SessionResponse:
        """Create a new quantum session.

        Args:
            backend_id: The backend identifier for the session.
            provider: The quantum provider enum or string.
            mode: The session mode (batch or dedicated).
            ttl: Time to live in seconds (optional).
            metadata: Additional metadata for the session (optional).
            sdk_provider: The SDK provider (QISKIT or BRAKET, optional).

        Returns:
            SessionResponse: The created session details.

        Raises:
            PlanqkClientError: If session creation fails.
            InvalidAccessTokenError: If authentication fails.
        """
        headers = {"content-type": "application/json"}

        # Create session request object
        request = CreateSessionRequest(
            backend_id=backend_id,
            provider=provider,
            mode=mode,
            ttl=ttl,
            metadata=metadata,
            sdk_provider=sdk_provider
        )

        # Convert to dict with proper serialization
        request_data = self._remove_none_values(request.model_dump())

        response = self.perform_request(requests.post, f"{base_url()}/sessions",
                                      data=request_data, headers=headers)
        return SessionResponse(**response)

    def get_session(self, session_id: str) -> SessionResponse:
        """Retrieve session details by session ID.

        Args:
            session_id: The unique session identifier.

        Returns:
            SessionResponse: The session details.

        Raises:
            PlanqkClientError: If session retrieval fails.
            InvalidAccessTokenError: If authentication fails.
        """
        response = self.perform_request(requests.get, f"{base_url()}/sessions/{session_id}")
        return SessionResponse(**response)

    def close_session(self, session_id: str) -> None:
        """Close a quantum session.

        Closes the session gracefully by preventing new jobs from being accepted while allowing
        existing jobs to complete.

        Args:
            session_id: The unique session identifier.

        Raises:
            PlanqkClientError: If session closure fails.
            InvalidAccessTokenError: If authentication fails.
        """
        payload = {"accept_jobs": False}
        self.perform_request(requests.patch, f"{base_url()}/sessions/{session_id}", data=payload)

    def cancel_session(self, session_id: str) -> None:
        """Cancel a quantum session.

        Cancel a session immediately, terminating any running or queued jobs
        within the session. This is more forceful than close_session which
        allows jobs to complete gracefully.

        Args:
            session_id: The unique session identifier.

        Raises:
            PlanqkClientError: If session cancellation fails.
            InvalidAccessTokenError: If authentication fails.
        """
        self.perform_request(requests.post, f"{base_url()}/sessions/{session_id}/cancel")

    def _get_default_headers(self):
        headers = {"x-auth-token": self._credentials.get_access_token()}

        # inject service execution if present
        if service_execution_id() is not None:
            headers["x-planqk-service-execution-id"] = service_execution_id()

        if self._context_resolver is None:
            self._context_resolver = ContextResolver()

        context = self._context_resolver.get_context()

        if self._organization_id is not None:
            headers["x-organizationid"] = self._organization_id
        elif context is not None and context.is_organization:
            headers["x-organizationid"] = context.get_organization_id()

        headers[HEADER_CLOUD_TRACE_CTX] = self._generate_trace_id()
        logger.debug("PLANQK client request trace id: %s", headers[HEADER_CLOUD_TRACE_CTX])

        return headers

    @classmethod
    def _remove_none_values(cls, d):
        if not isinstance(d, dict):
            return d
        return {k: cls._remove_none_values(v) for k, v in d.items() if v is not None}

    @classmethod
    def _generate_trace_id(cls):
        return '{:032x}'.format(random.getrandbits(128))
