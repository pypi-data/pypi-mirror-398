import json
import urllib.request
from typing import Optional

from braket.aws import AwsDevice
from braket.circuits.gate_calibrations import GateCalibrations
from braket.device_schema.rigetti.rigetti_device_capabilities_v2 import RigettiDeviceCapabilities

from planqk.quantum.sdk.braket.braket_provider import PlanqkBraketProvider
from planqk.quantum.sdk.braket.gate_based_device import PlanqkAwsGateBasedDevice


@PlanqkBraketProvider.register_device("aws.rigetti.ankaa")
class PlanqkAwsRigettiAnkaaDevice(PlanqkAwsGateBasedDevice):
    """PLANQK device wrapper for Rigetti Ankaa QPU with gate calibration support."""

    @property
    def name(self) -> str:
        return "Ankaa-3"

    @property
    def provider_name(self) -> str:
        return "Rigetti"

    @property
    def properties(self) -> RigettiDeviceCapabilities:
        """RigettiDeviceCapabilities: Return the device properties"""
        config = self._get_backend_config()
        return RigettiDeviceCapabilities.parse_raw(json.dumps(config))

    @property
    def gate_calibrations(self) -> Optional[GateCalibrations]:
        """Returns calibration data for Rigetti Ankaa QPU.

        Calibration data enables parameter restrictions in Target construction,
        allowing gate substitutions like rx(π) → x, rx(π/2) → sx, rx(-π/2) → sxdg.

        If calibrations are not cached, fetches them. Users can call
        refresh_gate_calibrations() to get fresh data.

        Returns:
            Optional[GateCalibrations]: The calibration object, or None if unavailable.
        """
        if not self._gate_calibrations:
            self._gate_calibrations = self.refresh_gate_calibrations()
        return self._gate_calibrations

    def refresh_gate_calibrations(self) -> Optional[GateCalibrations]:
        """Fetches gate calibrations from nativeGateCalibrationsRef URL.

        Uses Braket SDK's private parsing methods for compatibility.

        Returns:
            Optional[GateCalibrations]: The calibration data, or None if unavailable.
        """
        props = self.properties
        if (
            hasattr(props, "pulse")
            and hasattr(props.pulse, "nativeGateCalibrationsRef")
            and props.pulse.nativeGateCalibrationsRef
        ):
            try:
                url = props.pulse.nativeGateCalibrationsRef.split("?")[0]
                with urllib.request.urlopen(url, timeout=30) as f:  # noqa: S310
                    calibration_data = json.loads(f.read().decode("utf-8"))
                    # Use Braket SDK's private parsing method for compatibility
                    parsed = AwsDevice._parse_calibration_json(self, calibration_data)
                    return GateCalibrations(parsed)
            except (urllib.error.URLError, KeyError, AttributeError, ValueError, TimeoutError):
                # URLError: network issues
                # KeyError: missing frames in config
                # AttributeError: None values during parsing
                # ValueError: instruction parsing errors
                # TimeoutError: request timeout
                return None
        return None
