from typing import Optional, TYPE_CHECKING

from planqk.quantum.sdk.backend import PlanqkBackend
from planqk.quantum.sdk.client.client import _PlanqkClient
from planqk.quantum.sdk.client.job_dtos import JobDto
from planqk.quantum.sdk.client.model_enums import Provider

if TYPE_CHECKING:
    from planqk.quantum.sdk.qiskit.provider import PlanqkQuantumProvider
from planqk.quantum.sdk.qiskit.job import PlanqkQiskitJob
from planqk.quantum.sdk.qiskit.planqk_qiskit_runtime_job import PlanqkRuntimeJobV2
from planqk.quantum.sdk.qiskit.providers.aws.aws_qiskit_job import PlanqkAwsQiskitJob
from planqk.quantum.sdk.qiskit.providers.azure.azure_qiskit_job import PlanqkAzureQiskitJob
from planqk.quantum.sdk.qiskit.providers.qryd.qryd_qiskit_job import PlanqkQrydQiskitJob
from planqk.quantum.sdk.qiskit.providers.qudora.qudora_sim_job import PlanqkQudoraQiskitJob
from planqk.quantum.sdk.qiskit.providers.iqm.iqm_qiskit_job import PlanqkIqmQiskitJob


class PlanqkQiskitJobFactory:
    @staticmethod
    def create_job(backend: Optional[PlanqkBackend], job_id: Optional[str] = None, job_details: Optional[JobDto] = None,
                   planqk_client: Optional[_PlanqkClient] = None, provider: Optional["PlanqkQuantumProvider"] = None) -> PlanqkQiskitJob:

        provider_enum = PlanqkQiskitJobFactory._get_provider(backend, job_details)

        if not provider_enum:
            raise ValueError("Provider information is missing. Either 'backend' or 'job_details' with the 'provider' attribute must be specified.")

        if provider_enum == Provider.AWS:
            return PlanqkAwsQiskitJob(backend, job_id, job_details, planqk_client)
        elif provider_enum == Provider.AZURE:
            return PlanqkAzureQiskitJob(backend, job_id, job_details, planqk_client)
        elif provider_enum == Provider.QRYD:
            return PlanqkQrydQiskitJob(backend, job_id, job_details, planqk_client)
        elif provider_enum == Provider.QUDORA:
            return PlanqkQudoraQiskitJob(backend, job_id, job_details, planqk_client)
        elif provider_enum == Provider.IQM:
            return PlanqkIqmQiskitJob(backend, job_id, job_details, planqk_client)
        elif provider_enum == Provider.IBM:
            return PlanqkRuntimeJobV2(backend=backend, job_id=job_id, job_details=job_details, planqk_client=planqk_client, provider=provider)
        else:
            return PlanqkQiskitJob(backend, job_id, job_details, planqk_client)

    @staticmethod
    def _get_provider(backend, job_details):
        if backend:
            provider = backend.backend_info.provider
        else:
            provider = job_details.provider if job_details else None
        return provider