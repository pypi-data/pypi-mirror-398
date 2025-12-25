from __future__ import annotations

import json
import os
from typing import Any
from uuid import UUID

from planqk.quantum.sdk import _PlanqkClient
from .iqm_client_sdk.iqm_client.iqm_client import IQMClient
from .iqm_client_sdk.iqm_client.models import (
    CalibrationSet,
    CircuitBatch,
    CircuitCompilationOptions,
    ClientLibrary,
    DynamicQuantumArchitecture,
    QualityMetricSet,
    RunCounts,
    RunRequest,
    RunResult,
    RunStatus,
    StaticQuantumArchitecture,
)

REQUESTS_TIMEOUT = float(os.environ.get("IQM_CLIENT_REQUESTS_TIMEOUT", 120.0))
DEFAULT_TIMEOUT_SECONDS = 900
SECONDS_BETWEEN_CALLS = float(os.environ.get("IQM_CLIENT_SECONDS_BETWEEN_CALLS", 1.0))


class _PlanqkIqmClient(IQMClient):
    """Adapter client bridging PLANQK platform to IQM SDK protocols.

    Inherits from IQMClient but routes calls through PLANQK's backend infrastructure,
    enabling IQMBackend to work within the PLANQK middleware while maintaining IQM SDK compatibility.
    """

    def __init__(self, planqk_client: _PlanqkClient, backend_id: str):
        """Initialize the PlanqkIqmClient with a Planqk client.

        Args:
            planqk_client: An instance of the Planqk client to be used for communication with the IQM platform.
        """
        self._planqk_client = planqk_client
        self._backend_id = backend_id

    def get_about(self) -> dict:
        """Return information about the IQM client."""
        raise NotImplementedError("Not implemented in PlanqkIqmClient.")

    def get_health(self) -> dict:
            """Return the status of the station control service."""
            raise NotImplementedError("Not implemented in PlanqkIqmClient.")


    def submit_circuits(
                self,
                circuits: CircuitBatch,
                *,
                qubit_mapping: dict[str, str] | None = None,
                custom_settings: dict[str, Any] | None = None,
                calibration_set_id: UUID | None = None,
                shots: int = 1,
                options: CircuitCompilationOptions | None = None,
        ) -> UUID:
        raise NotImplementedError("Not implemented in PlanqkIqmClient.")

    def create_run_request(
            self,
            circuits: CircuitBatch,
            *,
            qubit_mapping: dict[str, str] | None = None,
            custom_settings: dict[str, Any] | None = None,
            calibration_set_id: UUID | None = None,
            shots: int = 1,
            options: CircuitCompilationOptions | None = None,
    ) -> RunRequest:
        return super().create_run_request(
            circuits=circuits,
            qubit_mapping=qubit_mapping,
            custom_settings=custom_settings,
            calibration_set_id=calibration_set_id,
            shots=shots,
            options=options,
        )

    def submit_run_request(self, run_request: RunRequest) -> UUID:
        """Submit a run request for execution on a quantum computer.

        This is called in :meth:`submit_circuits` and does not need to be called separately in normal usage.

        Args:
            run_request: Run request to be submitted for execution.

        Returns:
            ID for the created job. This ID is needed to query the job status and the execution results.

        """
        raise NotImplementedError("Not implemented in PlanqkIqmClient.")

    def get_run(self, job_id: UUID, *, timeout_secs: float = REQUESTS_TIMEOUT) -> RunResult:
        """Query the status and results of a submitted job.

        Args:
            job_id: ID of the job to query.
            timeout_secs: Network request timeout (seconds).

        Returns:
            Result of the job (can be pending).

        Raises:
            CircuitExecutionError: IQM server specific exceptions
            HTTPException: HTTP exceptions

        """
        raise NotImplementedError("Not implemented in PlanqkIqmClient.")

    def get_run_status(self, job_id: UUID, *, timeout_secs: float = REQUESTS_TIMEOUT) -> RunStatus:
        """Query the status of a submitted job.

        Args:
            job_id: ID of the job to query.
            timeout_secs: Network request timeout (seconds).

        Returns:
            Job status.

        Raises:
            CircuitExecutionError: IQM server specific exceptions
            HTTPException: HTTP exceptions

        """
        raise NotImplementedError("Not implemented in PlanqkIqmClient.")

    def wait_for_compilation(self, job_id: UUID, timeout_secs: float = DEFAULT_TIMEOUT_SECONDS) -> RunResult:
        """Poll results until a job is either compiled, pending execution, ready, failed, aborted, or timed out.

        Args:
            job_id: ID of the job to wait for.
            timeout_secs: How long to wait for a response before raising an APITimeoutError (seconds).

        Returns:
            Job result.

        Raises:
            APITimeoutError: time exceeded the set timeout

        """
        raise NotImplementedError("Not implemented in PlanqkIqmClient.")

    def wait_for_results(self, job_id: UUID, timeout_secs: float = DEFAULT_TIMEOUT_SECONDS) -> RunResult:
        """Poll results until a job is either ready, failed, aborted, or timed out.

           Note that jobs handling on the server side is async and if we try to request the results
           right after submitting the job (which is usually the case)
           we will find the job is still pending at least for the first query.

        Args:
            job_id: ID of the job to wait for.
            timeout_secs: How long to wait for a response before raising an APITimeoutError (seconds).

        Returns:
            Job result.

        Raises:
            APITimeoutError: time exceeded the set timeout

        """
        raise NotImplementedError("Not implemented in PlanqkIqmClient.")

    def abort_job(self, job_id: UUID, *, timeout_secs: float = REQUESTS_TIMEOUT) -> None:
        """Abort a job that was submitted for execution.

        Args:
            job_id: ID of the job to be aborted.
            timeout_secs: Network request timeout (seconds).

        Raises:
            JobAbortionError: aborting the job failed

        """
        raise NotImplementedError("Not implemented in PlanqkIqmClient.")

    def get_static_quantum_architecture(self) -> StaticQuantumArchitecture:
        """Retrieve the static quantum architecture (SQA) from the server.

        Caches the result and returns it on later invocations.

        Returns:
            Static quantum architecture of the server.

        Raises:
            EndpointRequestError: did not understand the endpoint response
            ClientAuthenticationError: no valid authentication provided
            HTTPException: HTTP exceptions

        """
        raise NotImplementedError("Not implemented in PlanqkIqmClient.")

    def get_quality_metric_set(self, calibration_set_id: UUID | None = None) -> QualityMetricSet:
        """Retrieve the latest quality metric set for the given calibration set from the server.

        Args:
            calibration_set_id: ID of the calibration set for which the quality metrics are returned.
                If ``None``, the current default calibration set is used.

        Returns:
            Requested quality metric set.

        Raises:
            EndpointRequestError: did not understand the endpoint response
            ClientAuthenticationError: no valid authentication provided
            HTTPException: HTTP exceptions

        """
        raise NotImplementedError("Not implemented in PlanqkIqmClient.")

    def get_calibration_set(self, calibration_set_id: UUID | None = None) -> CalibrationSet:
        """Retrieve the given calibration set from the server.

        Args:
            calibration_set_id: ID of the calibration set to retrieve.
                If ``None``, the current default calibration set is retrieved.

        Returns:
            Requested calibration set.

        Raises:
            EndpointRequestError: did not understand the endpoint response
            ClientAuthenticationError: no valid authentication provided
            HTTPException: HTTP exceptions

        """
        raise NotImplementedError("Not implemented in PlanqkIqmClient.")

    def get_dynamic_quantum_architecture(self, calibration_set_id: UUID | None = None) -> DynamicQuantumArchitecture:
        """Retrieve the dynamic quantum architecture (DQA) for the given calibration set from the server.

        Caches the result and returns the same result on later invocations, unless ``calibration_set_id`` is ``None``.
        If ``calibration_set_id`` is ``None``, always retrieves the result from the server because the default
        calibration set may have changed.

        Args:
            calibration_set_id: ID of the calibration set for which the DQA is retrieved.
                If ``None``, use current default calibration set on the server.

        Returns:
            Dynamic quantum architecture corresponding to the given calibration set.

        Raises:
            EndpointRequestError: did not understand the endpoint response
            ClientAuthenticationError: no valid authentication provided
            HTTPException: HTTP exceptions

        """
        config = self._planqk_client.get_backend_config(self._backend_id)

        return DynamicQuantumArchitecture.model_validate_json(json.dumps(config))

    def get_feedback_groups(self) -> tuple[frozenset[str], ...]:
        """Retrieve groups of qubits that can receive real-time feedback signals from each other.

        Real-time feedback enables conditional gates such as `cc_prx`.
        Some hardware configurations support routing real-time feedback only between certain qubits.

        Returns:
            Feedback groups. Within a group, any qubit can receive real-time feedback from any other qubit in
                the same group. A qubit can belong to multiple groups.
                If there is only one group, there are no restrictions regarding feedback routing.

        Raises:
            EndpointRequestError: did not understand the endpoint response
            ClientAuthenticationError: no valid authentication provided
            HTTPException: HTTP exceptions

        """
        raise NotImplementedError("Not implemented in PlanqkIqmClient.")

    def get_run_counts(self, job_id: UUID, *, timeout_secs: float = REQUESTS_TIMEOUT) -> RunCounts:
        """Query the counts of an executed job.

        Args:
            job_id: ID of the job to query.
            timeout_secs: Network request timeout (seconds).

        Returns:
            Measurement results of the job in histogram representation.

        Raises:
            EndpointRequestError: did not understand the endpoint response
            ClientAuthenticationError: no valid authentication provided
            HTTPException: HTTP exceptions

        """
        raise NotImplementedError("Not implemented in PlanqkIqmClient.")

    def get_supported_client_libraries(self, timeout_secs: float = REQUESTS_TIMEOUT) -> dict[str, ClientLibrary] | None:
        """Retrieve information about supported client libraries from the server.

        Args:
            timeout_secs: Network request timeout (seconds).

        Returns:
            Mapping from library identifiers to their metadata.

        Raises:
            EndpointRequestError: did not understand the endpoint response
            ClientAuthenticationError: no valid authentication provided
            HTTPException: HTTP exceptions

        """
        return None

    def close_auth_session(self) -> bool:
        """Close the authentication session.

        This method is used to close the authentication session and clean up any resources associated with it.
        It is typically called when the client is no longer needed or when the user wants to log out.

        Returns:
            True if the session was successfully closed, False otherwise.

        Raises:
            NotImplementedError: If the method is not implemented in the subclass.
        """
        raise NotImplementedError("Not implemented in PlanqkIqmClient.")