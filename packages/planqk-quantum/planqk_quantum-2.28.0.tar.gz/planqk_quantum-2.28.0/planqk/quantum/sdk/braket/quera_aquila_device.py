import json
from typing import Union, Optional, Any, cast

from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation
from braket.circuits import GateCalibrations
from braket.device_schema.pulse.frame_v1 import Frame
from braket.device_schema.pulse.port_v1 import Port
from braket.device_schema.quera import QueraDeviceCapabilities
from networkx import DiGraph
from qiskit import QuantumCircuit

from planqk.quantum.sdk.backend import PlanqkBackend
from planqk.quantum.sdk.braket.aws_device import PlanqkAwsDevice
from planqk.quantum.sdk.braket.braket_provider import PlanqkBraketProvider
from planqk.quantum.sdk.braket.planqk_quantum_task import PlanqkAwsQuantumTask
from planqk.quantum.sdk.client.model_enums import JobInputFormat, PlanqkSdkProvider


@PlanqkBraketProvider.register_device("aws.quera.aquila")
class PlanqkQueraAquilaDevice(PlanqkAwsDevice):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def properties(self) -> QueraDeviceCapabilities:
        """QueraDeviceCapabilities: Return the device properties"""
        config = self._planqk_client.get_backend_config(self._backend_info.id)
        return QueraDeviceCapabilities.parse_raw(json.dumps(config))

    @property
    def name(self) -> str:
        return "Aquila"

    @property
    def provider_name(self) -> str:
        return "QuEra"

    @property
    def topology_graph(self) -> DiGraph:
        return None

    @property
    def frames(self) -> dict[str, Frame]:
        return {}

    @property
    def gate_calibrations(self) -> Optional[GateCalibrations]:
        return None

    @property
    def ports(self) -> dict[str, Port]:
        return {}

    def run(self, task_specification: AnalogHamiltonianSimulation, shots: Optional[int] = None, *args: Any, **kwargs: Any) -> PlanqkAwsQuantumTask:
        shots = shots if shots else PlanqkAwsDevice.DEFAULT_SHOTS_QPU
        # deactivate type hinting as generics are not supported in Python
        task = PlanqkBackend.run(self, job_input=task_specification, shots=shots, sdk_provider=PlanqkSdkProvider.BRAKET, *args, **kwargs)

        return cast(PlanqkAwsQuantumTask, task)

    def _convert_to_job_input(self, job_input: Union[QuantumCircuit, AnalogHamiltonianSimulation], options=None) -> dict:
        input_json = job_input.to_ir().json(exclude={'braketSchemaHeader'})
        return {"ahs_program": json.loads(input_json)}

    def _get_job_input_format(self) -> JobInputFormat:
        return JobInputFormat.BRAKET_AHS_PROGRAM
