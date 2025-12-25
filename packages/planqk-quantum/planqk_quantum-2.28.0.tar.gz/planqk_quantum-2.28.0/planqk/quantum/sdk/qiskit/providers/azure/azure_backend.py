from typing import Optional

from qiskit.circuit import Gate
from qiskit.circuit.library import get_standard_gate_name_mapping

from planqk.quantum.sdk.qiskit import PlanqkQiskitBackend


class PlanqkAzureQiskitBackend(PlanqkQiskitBackend):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _to_gate(self, name: str) -> Optional[Gate]:
        name = name.lower()

        qiskit_gate_mapping = get_standard_gate_name_mapping()
        if name in qiskit_gate_mapping:
            return qiskit_gate_mapping[name]

    def _get_single_qubit_gate_properties(self, instr_name: Optional[str] = None) -> dict:
        if instr_name in {"measure", "delay"}:
            qubits = self.backend_info.configuration.qubits
            return {(i,): None for i in range(len(qubits))}
        return {None: None}

    def _get_multi_qubit_gate_properties(self) -> dict:
        return {None: None}
