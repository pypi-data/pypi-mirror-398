from abc import ABC
from typing import Optional, Any, cast

from braket.aws import AwsDevice
from braket.circuits import Circuit, Instruction
from braket.circuits.circuit_helpers import validate_circuit_and_shots
from braket.circuits.compiler_directives import StartVerbatimBox
from braket.circuits.gates import PulseGate
from braket.circuits.serialization import QubitReferenceType, OpenQASMSerializationProperties, IRType
from braket.device_schema import GateModelParameters
from braket.device_schema.ionq import IonqDeviceParameters
from braket.device_schema.pulse.frame_v1 import Frame
from braket.device_schema.pulse.port_v1 import Port
from braket.device_schema.rigetti import RigettiDeviceParameters
from braket.device_schema.simulators import GateModelSimulatorDeviceParameters
from braket.error_mitigation import ErrorMitigation
from qiskit import QuantumCircuit

from planqk.quantum.sdk.backend import PlanqkBackend
from planqk.quantum.sdk.braket.aws_device import PlanqkAwsDevice
from planqk.quantum.sdk.braket.planqk_quantum_task import PlanqkAwsQuantumTask
from planqk.quantum.sdk.client.model_enums import JobInputFormat, HardwareProvider, PlanqkSdkProvider


class PlanqkAwsGateBasedDevice(PlanqkAwsDevice, ABC):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._frames = None
        self._ports = None
        self._gate_calibrations = None

    @property
    def frames(self) -> dict[str, Frame]:
        """Returns a dict mapping frame ids to the frame objects for predefined frames
        for this device.
        """
        AwsDevice._update_pulse_properties(self)
        return self._frames or {}

    @property
    def ports(self) -> dict[str, Port]:
        """Returns a dict mapping port ids to the port objects for predefined ports
        for this device.
        """
        AwsDevice._update_pulse_properties(self)
        return self._ports or {}

    def run(self, task_specification: QuantumCircuit, shots: Optional[int] = None, *args: Any, **kwargs: Any) -> PlanqkAwsQuantumTask:
        shots = shots if shots else PlanqkAwsDevice.DEFAULT_SHOTS_QPU
        task = PlanqkBackend.run(self, job_input=task_specification, shots=shots, sdk_provider=PlanqkSdkProvider.BRAKET, *args, **kwargs)
        return cast(PlanqkAwsQuantumTask, task)

    def _convert_to_job_input(self, circuit: Circuit, options=None) -> dict:
        """
        Transform the Braket circuit to Braket QASM format.

        Adapted from the Braket SDK's aws_quantum_task.py module.

        Original source:
        Amazon Braket SDK for Python (Apache-2.0 License)
        GitHub Repository: https://github.com/amazon-braket/amazon-braket-sdk-python/blob/main/src/braket/aws/aws_quantum_task.py
        """
        validate_circuit_and_shots(circuit, options.get("shots"))
        disable_qubit_rewiring = options.get("disable_qubit_rewiring", False)
        gate_definitions = options.get("gate_definitions", {})

        qubit_reference_type = QubitReferenceType.VIRTUAL

        if (
            disable_qubit_rewiring
            or Instruction(StartVerbatimBox()) in circuit.instructions
            or gate_definitions
            or any(isinstance(instruction.operator, PulseGate) for instruction in circuit.instructions)
        ):
            qubit_reference_type = QubitReferenceType.PHYSICAL

        serialization_properties = OpenQASMSerializationProperties(
            qubit_reference_type=qubit_reference_type
        )

        openqasm_program = circuit.to_ir(
            ir_type=IRType.OPENQASM,
            serialization_properties=serialization_properties,
            gate_definitions=gate_definitions,
        )

        return openqasm_program.source

    def _circuit_device_params_from_dict(self, device_parameters: dict,
                                         paradigm_parameters: GateModelParameters) -> GateModelSimulatorDeviceParameters:
        if "errorMitigation" in device_parameters:
            error_migitation = device_parameters["errorMitigation"]
            device_parameters["errorMitigation"] = (
                error_migitation.serialize()
                if isinstance(error_migitation, ErrorMitigation)
                else error_migitation
            )
        hardware_provider = self._backend.backend_info.hardware_provider
        if hardware_provider == HardwareProvider.IONQ:
            return IonqDeviceParameters(paradigmParameters=paradigm_parameters, **device_parameters)
        if hardware_provider == HardwareProvider.RIGETTI:
            return RigettiDeviceParameters(paradigmParameters=paradigm_parameters)
        return GateModelSimulatorDeviceParameters(paradigmParameters=paradigm_parameters)

    def _convert_to_job_params(self, job_input: QuantumCircuit = None, options=None) -> dict:
        return {"disable_qubit_rewiring": options.get("disable_qubit_rewiring", False)}

    def _get_job_input_format(self) -> JobInputFormat:
        return JobInputFormat.BRAKET_OPEN_QASM_V3
