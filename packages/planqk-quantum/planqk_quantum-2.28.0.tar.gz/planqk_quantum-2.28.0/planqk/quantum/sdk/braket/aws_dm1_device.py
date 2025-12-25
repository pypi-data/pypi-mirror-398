import json

from braket.device_schema.simulators import GateModelSimulatorDeviceCapabilities

from planqk.quantum.sdk.braket.braket_provider import PlanqkBraketProvider
from planqk.quantum.sdk.braket.gate_based_device import PlanqkAwsGateBasedDevice


@PlanqkBraketProvider.register_device("aws.sim.dm1")
class PlanqkAwsDm1Device(PlanqkAwsGateBasedDevice):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def properties(self) -> GateModelSimulatorDeviceCapabilities:
        """GateModelSimulatorDeviceCapabilities: Return the device properties"""
        config = self._get_backend_config()
        return GateModelSimulatorDeviceCapabilities.parse_raw(json.dumps(config))

    @property
    def name(self) -> str:
        return "dm1"

    @property
    def provider_name(self) -> str:
        return "Amazon Braket"
