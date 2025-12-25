from typing import Union, Optional

from braket.ahs import AnalogHamiltonianSimulation
from qiskit import QuantumCircuit, qasm2
from qiskit.circuit.library import get_standard_gate_name_mapping
from qiskit.transpiler import InstructionProperties

from planqk.quantum.sdk.client.model_enums import JobInputFormat
from planqk.quantum.sdk.qiskit import PlanqkQiskitBackend
from planqk.quantum.sdk.qiskit import PlanqkQuantumProvider
from planqk.quantum.sdk.qiskit.options import OptionsV2


@PlanqkQuantumProvider.register_backend("qudora.sim.xg1")
class PlanqkQudoraSimXg1Backend(PlanqkQiskitBackend):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def _default_options(cls):
        return OptionsV2(
            shots=100
        )

    def _to_gate(self, name: str):
        name = name.lower()

        qiskit_gate_mapping = get_standard_gate_name_mapping()
        if name in qiskit_gate_mapping:
            return qiskit_gate_mapping[name]

    def _get_single_qubit_gate_properties(self, instr_name: Optional[str] = None) -> dict:
        if instr_name in {"measure", "delay"}:
            return {
                (i,): InstructionProperties(duration=1e-3, error=1e-3) for i in range(self._num_qubits())
            }

        return {
            (i,): InstructionProperties(duration=1e-4, error=1e-4) for i in range(self._num_qubits())
        }

    def _get_multi_qubit_gate_properties(self):
        return {
            (i, j): InstructionProperties(duration=1e-3, error=1e-4) for i in range(self._num_qubits()) for j in range(self._num_qubits())
        }

    def _convert_to_job_input(self, job_input: Union[QuantumCircuit, AnalogHamiltonianSimulation], options=None) -> dict:
        if isinstance(job_input, QuantumCircuit):
            return qasm2.dumps(job_input)
        raise TypeError(f"Cannot convert object of type {type(job_input)} to QuantumCircuit")

    def _convert_to_job_params(self, job_input: QuantumCircuit = None, options=None) -> dict:
        params = {}
        if options and hasattr(options, "backend_settings"):
            params["backend_settings"] = options.backend_settings
        return params

    def _get_job_input_format(self) -> JobInputFormat:
        return JobInputFormat.OPEN_QASM_V2
