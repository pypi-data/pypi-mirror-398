import logging
import time
from abc import ABC
from typing import Optional, Dict, Any

from planqk.quantum.sdk.client.client import _PlanqkClient
from planqk.quantum.sdk.client.job_dtos import JobDto
from planqk.quantum.sdk.client.model_enums import PlanqkJobStatus, PLANQK_JOB_FINAL_STATES
from planqk.quantum.sdk.exceptions import PlanqkError

logger = logging.getLogger(__name__)


class PlanqkBaseJob(ABC):

    def __init__(self, backend: Optional, job_id: Optional[str] = None, job_details: Optional[JobDto] = None,
                 planqk_client: Optional[_PlanqkClient] = None):
        self._client = planqk_client
        if self._client is None:
            raise RuntimeError("planqk_client must not be None")

        if job_id is None and job_details is None:
            raise ValueError("Either 'job_id', 'job_details' or both must be provided.")

        self._result = None
        self._backend = backend
        self._job_details = job_details
        self._status = None

        if job_id is not None and job_details is None:
            self._refresh(job_id)
        elif job_id is None and job_details is not None:
            self._submit()
        else:
            self._job_details = job_details

    def _submit(self):
        """
        Submits the job for execution.
        """

        if self._job_details is None:
            raise RuntimeError("Cannot submit job as no job details are set.")

        self._job_details = self._client.submit_job(self._job_details)

    def _result_states(self) -> set[PlanqkJobStatus]:
        """Returns the set of job states that are considered final for result retrieval."""
        return {PlanqkJobStatus.COMPLETED}

    def _result(self) -> any:
        """Polls for the job result until the job has completed successfully and returns the result.

        Returns:
            The job result if the job completed successfully. The result format is backend specific.

        Raises:
            An error if the job did reach another end state as `JOB_STATUS.COMPLETED`
        """
        if self._result is not None:
            return self._result

        status = self._update_state()
        if status not in PLANQK_JOB_FINAL_STATES:
            status = self._wait_for_final_state()

        if status in self._result_states():
            self._result = self._client.get_job_result(self.id)
            return self._result

        if status == PlanqkJobStatus.FAILED: #TODO error data should not be set but only retrieved via get_job_result
            if self._job_details.error_data is None:
                error_result_data = self._client.get_job_result(self.id)
                self._job_details.error_data = error_result_data
            msg = (
                f"Cannot retrieve results because the job execution failed with status '{status.name}'."
            )
            if self._job_details.error_data:
                msg += f" Reason: {self._job_details.error_data}."
            raise RuntimeError(msg)

        raise RuntimeError(
            f'{"Cannot retrieve results as job execution has not completed."}'
            + f"(status: {self._status}.")

    def _wait_for_final_state(self, timeout: Optional[float] = None, wait: float = 5) -> PlanqkJobStatus:
        """Poll the job status until it progresses to a final state such as ``DONE`` or ``ERROR``.

        Args:
            timeout: Seconds to wait for the job. If ``None``, wait indefinitely.
            wait: Seconds between queries.
            callback: Callback function invoked after each query.
                The following positional arguments are provided to the callback function:

                * job_id: Job ID
                * job_status: Status of the job from the last query
                * job: This BaseJob instance

                Note: different subclass might provide different arguments to
                the callback function.

        Raises:
            JobTimeoutError: If the job does not reach a final state before the
                specified timeout.
        """
        start_time = time.time()
        status = self._update_state()
        while status not in PLANQK_JOB_FINAL_STATES:
            logger.debug('Waiting for job %s to complete for retrieving its result. Current job status %s', self.id, status)
            elapsed_time = time.time() - start_time
            if timeout is not None and elapsed_time >= timeout:
                raise PlanqkError(f"Timeout while waiting for job {self.id}.")
            time.sleep(wait)
            status = self._update_state()
        return status

    def _update_state(self, use_cached_value: bool = False) -> PlanqkJobStatus:
        """
        Return the status of the job.

        Args:
            use_cached_value (bool): If `True`, uses the value most recently retrieved from PLANQK.
        """
        if not use_cached_value and self._status not in PLANQK_JOB_FINAL_STATES:
            self._status = self._client.get_job_status(self.id)

        return self._status

    @property
    def id(self) -> str:
        """
        This job's id.
        """
        return self._job_details.id if self._job_details is not None else None

    def job_id(self) -> str:
        """
        This job's id.
        """
        return self.id

    @property
    def shots(self) -> int:
        return self._job_details.shots

    def cancel(self):
        """
        Attempt to cancel the job.
        """
        self._client.cancel_job(self.id)

    def _refresh(self, job_id: str = None):
        """
        Refreshes the job details from the server.
        """
        if job_id is None and self.id is None:
            raise ValueError("Job Id is not set.")

        job_id = job_id if job_id is not None else self.id
        self._job_details = self._client.get_job(job_id)
        self._update_state()

    def calibration(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve the backend calibration that was effective when the job execution started.

        Note:
            The backend calibration data is unavailable if the job was executed on a simulator
            or if the job has not been executed yet.

        Returns:
            Optional[Dict[str, Any]]: Backend calibration data or None if no calibration data is available.
            The data format is backend specific.
        """
        return self._client.get_job_calibration(self.id)
