import json
import logging
from typing import Optional

from qiskit.providers import Backend, JobStatus
from qiskit.result.models import ExperimentResult, ExperimentResultData

from planqk.quantum.sdk.client.client import _PlanqkClient
from planqk.quantum.sdk.client.job_dtos import JobDto
from planqk.quantum.sdk.qiskit import PlanqkQiskitJob


class PlanqkQudoraQiskitJob(PlanqkQiskitJob):

    def __init__(self, backend: Optional[Backend], job_id: Optional[str] = None, job_details: Optional[JobDto] = None,
                 planqk_client: Optional[_PlanqkClient] = None):

        super().__init__(backend, job_id, job_details, planqk_client)

    def _create_experiment_result(self, provider_result: dict) -> ExperimentResult:

        if len(provider_result) > 1:
            logging.warn("Multi experiment results are not supported.")
        elif len(provider_result) == 0:
            logging.warn("No experiment results found.")
            return None

        counts = json.loads(provider_result[0])

        return ExperimentResult(
            shots=self.shots,
            success=True,
            status=JobStatus.DONE.name,
            data=ExperimentResultData(
                counts=counts,
                memory=[]
            )
        )
