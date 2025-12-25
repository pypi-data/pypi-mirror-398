from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from planqk.quantum.sdk.braket.aws_device import PlanqkAwsDevice

from braket.circuits import Circuit, Instruction
from braket.circuits.circuit_helpers import validate_circuit_and_shots
from braket.circuits.compiler_directives import StartVerbatimBox
from braket.circuits.gates import PulseGate
from braket.circuits.serialization import QubitReferenceType, OpenQASMSerializationProperties, IRType
from braket.ir.openqasm import Program as OpenQASMProgram
from qiskit import QuantumCircuit
from qiskit.providers import Options
from qiskit.transpiler import Target
from braket.device_schema import DeviceActionType
from qiskit_braket_provider.providers.adapter import (
    aws_device_to_target,
    gateset_from_properties,
    native_gate_set,
    to_braket,
)

from planqk.quantum.sdk.client.model_enums import JobInputFormat
from planqk.quantum.sdk.qiskit import PlanqkQiskitBackend
from planqk.quantum.sdk.qiskit.options import OptionsV2
from planqk.quantum.sdk.qiskit.provider import PlanqkQuantumProvider


@PlanqkQuantumProvider.register_backend("aws.ionq.aria")
@PlanqkQuantumProvider.register_backend("aws.ionq.forte")
@PlanqkQuantumProvider.register_backend("aws.sim.dm1")
@PlanqkQuantumProvider.register_backend("aws.sim.sv1")
class PlanqkAwsBackend(PlanqkQiskitBackend):

    def __init__(self, **kwargs):
        self._aws_device = None
        super().__init__(**kwargs)

    @property
    def _device(self) -> "PlanqkAwsDevice":
        """Lazy-initialize the AWS device for target construction and gateset retrieval."""
        if self._aws_device is None:
            from planqk.quantum.sdk.braket.braket_provider import PlanqkBraketProvider
            device_class = PlanqkBraketProvider.get_device_class(self.backend_info.id)
            self._aws_device = device_class(
                planqk_client=self._planqk_client,
                backend_info=self.backend_info
            )
        return self._aws_device

    @classmethod
    def _default_options(cls):
        return OptionsV2()

    def _planqk_backend_to_target(self) -> Target:
        """Constructs Target using qiskit-braket-provider's adapter.

        Uses the cached _device instance and delegates to aws_device_to_target()
        which reads native gates from properties.paradigm.nativeGateSet.

        TODO: Add gate_calibrations support for rx -> sx/sxdg/x substitutions
        """
        return aws_device_to_target(self._device)

    @property
    def num_qubits(self) -> int:
        """Return the number of qubits the backend has."""
        # For IQM Garnet backends the qubit size derived from the target is invalid (as they don't use zero-based qubit indices)
        return len(self.backend_info.configuration.qubits)

    def _to_gate(self, name: str):
        """Not used - Target is built via aws_device_to_target()."""
        pass

    def _get_single_qubit_gate_properties(self, instr_name=None):
        """Not used - Target is built via aws_device_to_target()."""
        pass

    def _get_multi_qubit_gate_properties(self):
        """Not used - Target is built via aws_device_to_target()."""
        pass

    def get_gateset(self, native: bool = False) -> Optional[set[str]]:
        """Get the gate set of the device.

        Mirrors qiskit-braket-provider's BraketBackend.get_gateset() API.

        Args:
            native: If True, return only native gates (for verbatim mode).
                   If False, return basis gates (supportedOperations for server-side compilation).

        Returns:
            The requested gate set as Qiskit gate names, or None if not available.
        """
        if native:
            return native_gate_set(self._device.properties)
        else:
            action = self._device.properties.action.get(DeviceActionType.OPENQASM)
            if not action:
                raise ValueError(f"Backend {self.name} does not support OpenQASM")
            return gateset_from_properties(action)

    def _convert_to_job_input(self, job_input: QuantumCircuit, options: Options = None):
        shots = options.get("shots", 1)
        inputs = options.get("inputs", {})
        verbatim = options.get("verbatim", False)

        # Use all supported gates for non-verbatim mode (server-side compilation)
        # This mirrors qiskit-braket-provider's _target_and_basis_gates() behavior
        basis_gates = self.get_gateset(native=False) if not verbatim else None
        braket_circuit = to_braket(job_input, basis_gates, verbatim=verbatim)

        validate_circuit_and_shots(braket_circuit, shots)

        return self._transform_braket_to_qasm_3_program(braket_circuit, False, inputs)

    def _get_job_input_format(self) -> JobInputFormat:
        return JobInputFormat.BRAKET_OPEN_QASM_V3

    def _convert_to_job_params(self, job_input=None, options=None) -> dict:
        return {'disable_qubit_rewiring': False}

    def _transform_braket_to_qasm_3_program(self, braket_circuit: Circuit,
                                            disable_qubit_rewiring: bool,
                                            inputs: Dict[str, float]) -> str:
        """Transforms a Braket input to a QASM 3 program."""

        qubit_reference_type = QubitReferenceType.VIRTUAL

        if (
            disable_qubit_rewiring
            or Instruction(StartVerbatimBox()) in braket_circuit.instructions
            or any(isinstance(instruction.operator, PulseGate) for instruction in braket_circuit.instructions)
        ):
            qubit_reference_type = QubitReferenceType.PHYSICAL

        serialization_properties = OpenQASMSerializationProperties(
            qubit_reference_type=qubit_reference_type
        )

        openqasm_program = braket_circuit.to_ir(
            ir_type=IRType.OPENQASM, serialization_properties=serialization_properties
        )
        if inputs:
            inputs_copy = openqasm_program.inputs.copy() if openqasm_program.inputs is not None else {}
            inputs_copy.update(inputs)
            openqasm_program = OpenQASMProgram(
                source=openqasm_program.source,
                inputs=inputs_copy,
            )

        return openqasm_program.source
