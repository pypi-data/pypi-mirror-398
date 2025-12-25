from typing import Optional

from qiskit.result.models import ExperimentResult

from planqk.quantum.sdk.client.client import _PlanqkClient
from planqk.quantum.sdk.client.job_dtos import JobDto
from planqk.quantum.sdk.client.model_enums import HardwareProvider
from planqk.quantum.sdk.qiskit import PlanqkQiskitJob, PlanqkQiskitBackend
from planqk.quantum.sdk.qiskit.providers.azure.result.ionq_result_formatter import IonqResultFormatter
from planqk.quantum.sdk.qiskit.providers.azure.result.microsoft_v2_result_formatter import MicrosoftV2ResultFormatter


class PlanqkAzureQiskitJob(PlanqkQiskitJob):

    def __init__(self, backend: Optional[PlanqkQiskitBackend], job_id: Optional[str] = None, job_details: Optional[JobDto] = None,
                 planqk_client: Optional[_PlanqkClient] = None):

        super().__init__(backend, job_id, job_details, planqk_client)

    def _create_experiment_result(self, provider_result: dict) -> ExperimentResult:
        backend: PlanqkQiskitBackend = self.backend()
        hw_provider = backend.backend_info.hardware_provider

        if hw_provider == HardwareProvider.IONQ:
            formatter = IonqResultFormatter(provider_result, self)
        elif hw_provider == HardwareProvider.QUANTINUUM:
            formatter = MicrosoftV2ResultFormatter(provider_result, self)
        else:
            raise NotImplementedError(f"Hardware provider {hw_provider} not supported")

        return formatter.format_result()
