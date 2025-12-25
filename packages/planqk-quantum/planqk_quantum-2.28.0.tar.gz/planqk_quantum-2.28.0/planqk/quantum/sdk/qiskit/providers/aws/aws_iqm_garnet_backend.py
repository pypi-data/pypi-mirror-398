from typing import List, Dict

from planqk.quantum.sdk.client.backend_dtos import QubitDto, ConnectivityDto
from planqk.quantum.sdk.qiskit.provider import PlanqkQuantumProvider
from planqk.quantum.sdk.qiskit.providers.aws.aws_backend import PlanqkAwsBackend


def _update_qubits_with_zero_based_ids(qubits: List[QubitDto]):
    for qubit in qubits:
        qubit.id = str(int(qubit.id) - 1)


def _update_connectivity_graph_with_zero_based_qubit_ids(connectivity: ConnectivityDto):
    graph = connectivity.graph
    updated_graph: Dict[str, List[str]] = {}
    for src, targets in graph.items():
        updated_graph[str(int(src) - 1)] = [str(int(target) - 1) for target in targets]

    connectivity.graph = updated_graph


@PlanqkQuantumProvider.register_backend("aws.iqm.garnet")
class PlanqkAwsIqmGarnetBackend(PlanqkAwsBackend):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _normalize_qubit_indices(self):
        _update_qubits_with_zero_based_ids(self.backend_info.configuration.qubits)
