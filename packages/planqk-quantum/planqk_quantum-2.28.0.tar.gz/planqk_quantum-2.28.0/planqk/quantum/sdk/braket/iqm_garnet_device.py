import json

from braket.device_schema.iqm import IqmDeviceCapabilities

from planqk.quantum.sdk.braket.braket_provider import PlanqkBraketProvider
from planqk.quantum.sdk.braket.gate_based_device import PlanqkAwsGateBasedDevice


@PlanqkBraketProvider.register_device("aws.iqm.garnet")
class PlanqkAwsIqmGarnetDevice(PlanqkAwsGateBasedDevice):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def name(self) -> str:
        return "Garnet"

    @property
    def provider_name(self) -> str:
        return "IQM"

    @property
    def properties(self) -> IqmDeviceCapabilities:
        """IqmDeviceCapabilities: Return the device properties"""
        config = self._get_backend_config()
        return IqmDeviceCapabilities.parse_raw(json.dumps(config))
