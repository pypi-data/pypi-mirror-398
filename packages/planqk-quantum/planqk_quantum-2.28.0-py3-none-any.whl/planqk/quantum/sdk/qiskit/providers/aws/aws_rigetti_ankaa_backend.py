from planqk.quantum.sdk.client.backend_dtos import QubitDto
from planqk.quantum.sdk.qiskit.provider import PlanqkQuantumProvider
from planqk.quantum.sdk.qiskit.providers.aws.aws_backend import PlanqkAwsBackend


@PlanqkQuantumProvider.register_backend("aws.rigetti.ankaa")
class PlanqkAwsRigettiAnkaaBackend(PlanqkAwsBackend):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _normalize_qubit_indices(self):
        qubits = [QubitDto(id=str(qubit_id)) for qubit_id in range(self.num_qubits)]
        self.backend_info.configuration.qubits = qubits
