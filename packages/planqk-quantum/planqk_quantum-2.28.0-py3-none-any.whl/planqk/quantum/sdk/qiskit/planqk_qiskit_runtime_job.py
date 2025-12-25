"""
PLANQK Runtime Job V2 Implementation

This class extends PlanqkRuntimeJob to provide full compatibility with IBM's 
RuntimeJobV2 interface, including all public methods from RuntimeJobV2 and its parent classes.
"""

import json
from datetime import datetime
from typing import Optional, Type, Any, Dict, Union, Sequence, List

from qiskit.providers import Backend
from qiskit_ibm_runtime import IBMError, RuntimeJobMaxTimeoutError, RuntimeJobFailureError, RuntimeInvalidStateError
from qiskit_ibm_runtime.constants import DEFAULT_DECODERS, API_TO_JOB_ERROR_MESSAGE
from qiskit_ibm_runtime.models.backend_properties import BackendProperties
from qiskit_ibm_runtime.runtime_job_v2 import JobStatus
from qiskit_ibm_runtime.utils import utc_to_local
from qiskit_ibm_runtime.utils.result_decoder import ResultDecoder

from planqk.quantum.sdk.client import PlanqkJobStatus
from planqk.quantum.sdk.client.client import _PlanqkClient
from planqk.quantum.sdk.client.job_dtos import JobDto
from planqk.quantum.sdk.client.model_enums import PLANQK_JOB_FINAL_STATES
from planqk.quantum.sdk.qiskit.job import PlanqkQiskitJob

JOB_STATUS_MAP: Dict[str, JobStatus] = {
    "CREATED": "INITIALIZING",
    "PENDING": "QUEUED",
    "RUNNING": "RUNNING",
    "COMPLETED": "DONE",
    "FAILED": "ERROR",
    "CANCELLING": "RUNNING",
    "CANCELLED": "CANCELLED",
    "UNKNOWN": "INITIALIZING",
}


class PlanqkRuntimeJobV2(PlanqkQiskitJob):
    """PLANQK Runtime Job V2 with full IBM RuntimeJobV2 compatibility.
    
    This class extends PlanqkRuntimeJob to provide full compatibility with IBM's 
    RuntimeJobV2 interface, including all public methods from RuntimeJobV2 and its parent classes.
    
    Args:
        backend: The backend the job was submitted to.
        job_id: Job ID.
        job_details: Job details from PLANQK.
        result_decoder: Result decoder for job results.
        planqk_client: PLANQK client instance.
        session_id: Job's session ID.
        program_id: ID of the program this job is for.
    """

    def __init__(
            self,
            backend: Optional[Backend],
            job_id: Optional[str] = None,
            job_details: Optional[JobDto] = None,
            result_decoder: Optional[Union[Type[ResultDecoder], Sequence[Type[ResultDecoder]]]] = None,
            planqk_client: Optional[_PlanqkClient] = None,
            session_id: Optional[str] = None,
            program_id: Optional[str] = None,
            provider: "PlanqkQiskitRuntimeService" = None
    ):
        # Validate mandatory provider parameter
        if provider is None:
            raise ValueError("provider parameter is required for PlanqkRuntimeJobV2")
        
        super().__init__(backend=backend, job_id=job_id, job_details=job_details, planqk_client=planqk_client)
        
        # Store provider for backend creation
        self._provider = provider

        # Set runtime-specific parameters from constructor parameters or job details
        self._session_id = session_id or (self._job_details.input_params.get('session_id', None) if self._job_details else None)
        self._program_id = program_id or (self._job_details.input_params.get('program_id', None) if self._job_details else None)

        # Set up result decoders (interim and final)
        decoder = result_decoder or DEFAULT_DECODERS.get(self._program_id, None) or ResultDecoder
        if isinstance(decoder, Sequence):
            self._interim_result_decoder, self._final_result_decoder = decoder
        else:
            self._interim_result_decoder = self._final_result_decoder = decoder

        self._error_message = None
        self._result = None


    def result(
            self,
            timeout: Optional[float] = None,
            decoder: Optional[Type[ResultDecoder]] = None,
    ) -> Any:
        """Return the results of the job.

        Args:
            timeout: Number of seconds to wait for job completion.
            decoder: A ResultDecoder subclass used to decode job results.

        Returns:
            Runtime job result decoded using the specified or default decoder.

        Raises:
            RuntimeJobFailureError: If the job failed.
            RuntimeJobMaxTimeoutError: If the job does not complete within given timeout.
            RuntimeInvalidStateError: If the job was cancelled, and attempting to retrieve result.
        """
        _decoder = decoder or self._final_result_decoder

        if self._result is None or (_decoder != self._final_result_decoder):
            self.wait_for_final_state(timeout=timeout)
            status = self.status()

            if status == "ERROR":
                error_message = self._reason if self._reason else self._error_message
                if self._reason == 1305:
                    raise RuntimeJobMaxTimeoutError(error_message)
                raise RuntimeJobFailureError(f"Unable to retrieve job result. {error_message}")

            if status == "CANCELLED":
                raise RuntimeInvalidStateError(
                    f"Unable to retrieve result for job {self.job_id()}. Job was cancelled."
                )

            result_raw = self._get_raw_result()
            self._result = _decoder.decode(json.dumps(result_raw)) if result_raw else None

        return self._result

    def status(self) -> JobStatus:
        """Return the status of the job.

        Returns:
            Status of this job.
        """
        self._set_status_and_error_message()
        return JOB_STATUS_MAP[self._status]

    def _get_raw_result(self) -> Dict:
        """Fetch raw job result from PLANQK. Returns error data if job failed."""
        try:
           return super()._result()
        except RuntimeError:
            return self._job_details.error_data

    def cancelled(self) -> bool:
        """Return whether the job has been cancelled.
        
        Returns:
            True if the job has been cancelled, False otherwise.
            
        """
        return self._update_state() == PlanqkJobStatus.CANCELLED

    def done(self) -> bool:
        """Return whether the job has successfully finished.
        
        Returns:
            True if the job has successfully finished, False otherwise.

        """
        return self._update_state() == PlanqkJobStatus.COMPLETED

    def running(self) -> bool:
        """Return whether the job is actively running.
        
        Returns:
            True if the job is actively running, False otherwise.
            
        """
        return self._update_state() == PlanqkJobStatus.RUNNING

    def in_final_state(self) -> bool:
        """Return whether the job is in a final job state such as DONE or ERROR.
        
        Returns:
            True if the job is in a final state, False otherwise.
            
        """
        return self._update_state() in PLANQK_JOB_FINAL_STATES

    def errored(self) -> bool:
        """Return whether the job has failed."""
        return self._update_state() == PlanqkJobStatus.FAILED

    def submit(self) -> None:
        """Submit the job to the backend for execution.
        
        Raises:
            NotImplementedError: Job submission is not supported for PLANQK runtime jobs V2.
        """
        raise NotImplementedError("Job submission is not supported for PLANQK runtime jobs V2. Use the primitive's run function instead.")

    # noinspection PyMethodOverriding
    def wait_for_final_state(self, timeout: Optional[float] = None) -> None:
        """Poll the job status until it progresses to a final state.
        
        Args:
            timeout: Seconds to wait for the job. If None, wait indefinitely.
        """
        self._wait_for_final_state(timeout=timeout)

    # Runtime Job Specific Methods (from IBM RuntimeJobV2)

    def queue_info(self) -> Optional[Dict[str, Any]]:
        """Return queue information for this job.
        
        Returns:
            Queue information for this job, or None if queue information is not available.
            
        Raises:
            NotImplementedError: Queue information is not supported for PLANQK runtime jobs V2.
        """
        raise NotImplementedError("Queue information is not supported for PLANQK runtime jobs V2.")

    def queue_position(self) -> Optional[int]:
        """Return the position of the job in the server queue.
        
        Returns:
            Position in the queue or None if position is not available.
            
        Raises:
            NotImplementedError: Queue position is not supported for PLANQK runtime jobs V2.
        """
        raise NotImplementedError("Queue position is not supported for PLANQK runtime jobs V2.")

    def error_message(self) -> Optional[str]:
        """Provide details about the reason of failure.
        
        Returns:
            An error report if the job failed or None otherwise.
            
        """
        self._set_status_and_error_message()
        return self._error_message

    def backend(self, timeout: Optional[float] = None) -> Optional[Backend]:
        """Return the backend for this job.
        
        Args:
            timeout: Optional timeout (not used in this implementation).
            
        Returns:
            Backend instance or None if backend cannot be created.
        """
        if self._backend is None and self._provider:
                self._backend = self._provider.backend(self._job_details.backend_id)
        return self._backend


    def _set_status_and_error_message(self) -> None:
        """Fetch and set status and error message."""
        if self._update_state() in {PlanqkJobStatus.FAILED, PlanqkJobStatus.CANCELLED}:
            error_data = self._get_raw_result()

            if error_data:
                self._set_status(error_data)
                self._set_error_message(error_data)

    def _set_status(self, job_result: Dict) -> None:
        """Set status.

        Args:
            job_result: Job response from runtime API.

        Raises:
            IBMError: If an unknown status is returned from the server.
        """
        try:
            reason = job_result.get("reason")
            reason_code = job_result.get("reasonCode")
            if reason:
                self._reason = reason
                if reason_code:
                    self._reason = f"Error code {reason_code}; {self._reason}"
                    self._reason_code = reason_code
            self._status = self._status_from_job_response()
        except KeyError:
            raise IBMError(f"Unknown status: {job_result['status']}")

    def _set_error_message(self, job_result: Dict) -> None:
        """Set error message if the job failed.

        Args:
            job_result: Job response from runtime API.
        """
        if self.errored():
            self._error_message = self._error_msg_from_job_response(str(job_result))
        else:
            self._error_message = None

    def _error_msg_from_job_response(self, job_response_str: str) -> str:
        """Returns the error message from an API response.

        Args:
            job_response_str: Job response from the runtime API.

        Returns:
            Error message.
        """

        index = job_response_str.rfind("Traceback")
        if index != -1:
            job_response_str = job_response_str[index:]

        if self.cancelled() and self._reason_code == 1305:
            error_msg = API_TO_JOB_ERROR_MESSAGE["CANCELLED - RAN TOO LONG"]
            return error_msg.format(self.job_id(), job_response_str)
        else:
            error_msg = API_TO_JOB_ERROR_MESSAGE["FAILED"]
            return error_msg.format(self.job_id(), self._reason or job_response_str)

    def _status_from_job_response(self) -> Union[JobStatus, str]:
        if self._status == PlanqkJobStatus.CANCELLED and self._reason_code == 1305:
            return PlanqkJobStatus.FAILED
        return self._status

    def scheduling_mode(self) -> Optional[str]:
        """Return the scheduling mode the job is in.
        
        Returns:
            Scheduling mode of the job or None.
            
        Raises:
            NotImplementedError: Scheduling mode is not supported for PLANQK runtime jobs V2.
        """
        raise NotImplementedError("Scheduling mode is not supported for PLANQK runtime jobs V2.")

    def usage_estimation(self) -> Dict[str, Any]:
        """Return the usage estimation infromation for this job.
        
        Returns:
            Usage estimation information.
            
        Raises:
            NotImplementedError: Usage estimation is not supported for PLANQK runtime jobs V2.
        """
        raise NotImplementedError("Usage estimation is not supported for PLANQK runtime jobs V2.")

    def update_name(self, name: str) -> str:
        """Update the name associated with this job.
        
        Args:
            name: The new name for this job.
            
        Returns:
            The new name associated with this job.
            
        Raises:
            NotImplementedError: Name update is not supported for PLANQK runtime jobs V2.
        """
        raise NotImplementedError("Name update is not supported for PLANQK runtime jobs V2.")

    def update_tags(self, replacement_tags: List[str]) -> List[str]:
        """Update the tags associated with this job.
        
        Args:
            replacement_tags: The new tags to associate with this job.
            
        Returns:
            The new tags associated with this job.
            
        Raises:
            NotImplementedError: Tag update is not supported for PLANQK runtime jobs V2.
        """
        raise NotImplementedError("Tag update is not supported for PLANQK runtime jobs V2.")

    def usage(self) -> float:
        """Return job usage in seconds.
        
        Note:
            This method is not implemented for PLANQK runtime jobs V2.
            
        Returns:
            Job usage in seconds.
            
        Raises:
            NotImplementedError: Usage tracking is not supported for PLANQK runtime jobs V2.
        """
        raise NotImplementedError("Usage tracking is not supported for PLANQK runtime jobs V2.")

    def metrics(self) -> Dict[str, Any]:
        """Return job metrics.
        
        Note:
            This method is not implemented for PLANQK runtime jobs V2.
            
        Returns:
            A dictionary with job metrics including timestamps and usage details.
            
        Raises:
            NotImplementedError: Metrics collection is not supported for PLANQK runtime jobs V2.
        """
        raise NotImplementedError("Metrics collection is not supported for PLANQK runtime jobs V2.")

    def logs(self) -> str:
        """Return job logs.
        
        Note:
            This method is not implemented for PLANQK runtime jobs V2.
            Job logs are only available after the job finishes.
            
        Returns:
            Job logs, including standard output and error.
            
        Raises:
            NotImplementedError: Log retrieval is not supported for PLANQK runtime jobs V2.
        """
        raise NotImplementedError("Log retrieval is not supported for PLANQK runtime jobs V2.")

    def properties(self, refresh: bool = False) -> Optional[BackendProperties]:
        """Return the backend properties for this job.

        Args:
            refresh: If ``True``, re-query the server for the backend properties.
                Otherwise, return a cached version.

        Returns:
            The backend properties used for this job, at the time the job was run,
            or ``None`` if properties are not available.
        """
        return self._backend.properties(refresh)

    # Properties from IBM RuntimeJobV2

    @property
    def name(self) -> Optional[str]:
        """Job name.
        
        Returns:
            Job name or None if not available.
       """
        return self.job_id()

    @property
    def tags(self) -> List[str]:
        """Job tags.
        
        Returns:
            Tags assigned to the job.
            
        Raises:
            NotImplementedError: Job tags are not supported for PLANQK runtime jobs V2.
        """
        raise NotImplementedError("Job tags are not supported for PLANQK runtime jobs V2.")

    @property
    def time_per_step(self) -> Optional[Dict[str, Any]]:
        """Return the time spent in each step (in seconds) of the job processing.
        
        Returns:
            Time spent in each step of the job processing or None if not available.
            
        Raises:
            NotImplementedError: Time per step is not supported for PLANQK runtime jobs V2.
        """
        raise NotImplementedError("Time per step is not supported for PLANQK runtime jobs V2.")

    @property
    def estimated_start_time(self) -> Optional[datetime]:
        """Return estimated start time of the job, in local time.
        
        Returns:
            Estimated start time of the job, or None if not available.
            
        Raises:
            NotImplementedError: Estimated start time is not supported for PLANQK runtime jobs V2.
        """
        raise NotImplementedError("Estimated start time is not supported for PLANQK runtime jobs V2.")

    @property
    def estimated_completion_time(self) -> Optional[datetime]:
        """Return estimated completion time of the job, in local time.
        
        Returns:
            Estimated completion time of the job, or None if not available.
            
        Raises:
            NotImplementedError: Estimated completion time is not supported for PLANQK runtime jobs V2.
        """
        raise NotImplementedError("Estimated completion time is not supported for PLANQK runtime jobs V2.")

    # Inherited properties that are already implemented or need V2-specific implementation

    @property
    def version(self) -> int:
        """Job version.
        
        Returns:
            Job version.
            
        Raises:
            NotImplementedError: Job version is not supported for PLANQK runtime jobs V2.
        """
        raise NotImplementedError("Job version is not supported for PLANQK runtime jobs V2.")

    @property
    def backend_version(self) -> str:
        """Backend version.
        
        Returns:
            Backend version used to run this job.
            
        Raises:
            NotImplementedError: Backend version is not supported for PLANQK runtime jobs V2.
        """
        raise NotImplementedError("Backend version is not supported for PLANQK runtime jobs V2.")

    @property
    def usage_estimation(self) -> Dict[str, Any]:
        """Return the usage estimation information for this job.

        Returns:
            ``quantum_seconds`` which is the estimated system execution time
            of the job in seconds. Quantum time represents the time that
            the system is dedicated to processing your job.
        Raises:
            NotImplementedError: Usage estimation is not supported for PLANQK runtime jobs V2.
        """
        raise NotImplementedError("Usage estimation is not supported for PLANQK runtime jobs V2.")

    @property
    def image(self) -> str:
        """Return the runtime image used for the job.

        Note:
            Currently, PLANQK does not support custom runtime images.

        Returns:
            Runtime image: image_name:tag or "" if the default
            image is used.
        """
        return ""

    @property
    def inputs(self) -> Dict:
        """Job input parameters.

        Returns:
            Input parameters used in this job.
        """
        if not self._job_details or self._job_details.input is None:
            return {}
        return self._job_details.input

    @property
    def primitive_id(self) -> str:
        """Primitive name.
        Returns:
            Primitive this job is for.
        """
        return self._program_id

    @property
    def creation_date(self) -> Optional[datetime]:
        """Job creation date in local time.

        Returns:
            The job creation date as a datetime object, in local time, or
            ``None`` if creation date is not available.
        """
        return utc_to_local(self._job_details.created_at)

    @property
    def session_id(self) -> str:
        """Session ID.

        Returns:
            Session ID. None if the backend is a simulator.
        """
        return self._session_id

    @property
    def instance(self) -> Optional[str]:
        """Return the IBM Cloud instance CRN.
         Note:
            This method is not implemented for PLANQK. Instance management
            is handled by the PLANQK platform.

        Returns:
            A list with instances available for the active account.
        """
        raise NotImplementedError("instances method not implemented. Instance management is handled by PLANQK platform.")

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}('{self._job_id}', '{self._program_id}')>"
