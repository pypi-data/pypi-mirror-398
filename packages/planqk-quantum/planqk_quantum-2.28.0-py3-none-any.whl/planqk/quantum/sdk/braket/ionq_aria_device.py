import json

from braket.device_schema.ionq import IonqDeviceCapabilities

from planqk.quantum.sdk.braket.braket_provider import PlanqkBraketProvider
from planqk.quantum.sdk.braket.gate_based_device import PlanqkAwsGateBasedDevice


@PlanqkBraketProvider.register_device("aws.ionq.aria")
class PlanqkAwsIonqDevice(PlanqkAwsGateBasedDevice):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def properties(self) -> IonqDeviceCapabilities:
        """IonqDeviceCapabilities: Return the device properties"""
        config = self._get_backend_config()
        return IonqDeviceCapabilities.parse_raw(json.dumps(config))

    @property
    def provider_name(self) -> str:
        return "IonQ"


@PlanqkBraketProvider.register_device("aws.ionq.forte")
class PlanqkAwsIonqForteDevice(PlanqkAwsIonqDevice):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def name(self) -> str:
        return "Forte 1"


@PlanqkBraketProvider.register_device("aws.ionq.aria")
class PlanqkAwsIonqAriaDevice(PlanqkAwsIonqDevice):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def name(self) -> str:
        return "Aria 1"
