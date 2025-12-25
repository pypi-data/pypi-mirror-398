import json
from typing import Optional

from braket.schema_common import BraketSchemaBase
from braket.tasks import GateModelQuantumTaskResult
from qiskit.providers import JobStatus, Backend
from qiskit.quantum_info import Statevector
from qiskit.result.models import ExperimentResult, ExperimentResultData

from planqk.quantum.sdk.client.client import _PlanqkClient
from planqk.quantum.sdk.client.job_dtos import JobDto
from planqk.quantum.sdk.qiskit import PlanqkQiskitJob


class PlanqkAwsQiskitJob(PlanqkQiskitJob):

    def __init__(self, backend: Optional[Backend], job_id: Optional[str] = None, job_details: Optional[JobDto] = None,
                 planqk_client: Optional[_PlanqkClient] = None):
        super().__init__(backend, job_id, job_details, planqk_client)

    def _create_experiment_result(self, provider_result: dict) -> ExperimentResult:
        """
        Transform the AWS Braket result to Qiskit result format.

        Adapted from the Braket SDK's braket_quantum_task.py module.

        Original source:
        Amazon Braket SDK for Python (Apache-2.0 License)
        GitHub Repository: https://github.com/qiskit-community/qiskit-braket-provider/blob/main/qiskit_braket_provider/providers/braket_quantum_task.py
        """
        gate_model_result = BraketSchemaBase.parse_raw_schema(json.dumps(provider_result))
        GateModelQuantumTaskResult.cast_result_types(gate_model_result)
        gate_model_result = GateModelQuantumTaskResult.from_object(gate_model_result)

        if gate_model_result.task_metadata.shots == 0:
            braket_statevector = gate_model_result.values[
                gate_model_result._result_types_indices[
                    "{'type': <Type.statevector: 'statevector'>}"
                ]
            ]
            data = ExperimentResultData(
                statevector=Statevector(braket_statevector).reverse_qargs().data,
            )
        else:
            counts = {
                k[::-1]: v for k, v in dict(gate_model_result.measurement_counts).items()
            }  # convert to little-endian

            data = ExperimentResultData(
                counts=counts,
                memory=[
                    "".join(shot_result[::-1].astype(str))
                    for shot_result in gate_model_result.measurements
                ],
            )

        experiment_result = ExperimentResult(
            shots=gate_model_result.task_metadata.shots,
            success=True,
            status=JobStatus.DONE.name,
            data=data,
        )

        return experiment_result
