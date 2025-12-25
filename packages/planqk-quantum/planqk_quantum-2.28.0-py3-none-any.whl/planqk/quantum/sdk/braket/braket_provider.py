from typing import Dict, Type, List

from planqk.quantum.sdk.braket.aws_device import PlanqkAwsDevice
from planqk.quantum.sdk.client.backend_dtos import BackendDto
from planqk.quantum.sdk.exceptions import BackendNotFoundError, PlanqkClientError
from planqk.quantum.sdk.qiskit.provider import _PlanqkProvider


class PlanqkBraketProvider(_PlanqkProvider):
    _device_mapping: Dict[str, Type[PlanqkAwsDevice]] = {}

    @classmethod
    def register_device(cls, device_id: str):
        """For internal use only. Binds a device class to a PLANQK backend id."""

        def decorator(device_cls: Type[PlanqkAwsDevice]):
            cls._device_mapping[device_id] = device_cls
            return device_cls

        return decorator

    @classmethod
    def get_device_class(cls, backend_id: str) -> Type[PlanqkAwsDevice]:
        device_class = cls._device_mapping.get(backend_id)
        if device_class is None:
            raise BackendNotFoundError(f"Backend '{backend_id}' is not supported by PLANQK Braket.")
        return device_class

    def get_device(self, backend_id: str) -> PlanqkAwsDevice:
        """
        Retrieves an AWS Braket Device based on the provided PLANQK backend id.

        Args:
            backend_id (str): The PLANQK backend (device) id.

        Returns:
            PlanqkAwsDevice: The AWS Braket device corresponding to the backend id.

        Raises:
            BackendNotFoundError: If the backend with the given id cannot be found or is not supported by the Braket SDK.

        Note:
            An overview of the supported backends and their IDs can be found at: https://platform.planqk.de/quantum-backends
        """
        backend_info = self._get_backend_info(backend_id)
        return self._get_planqk_braket_device(backend_info)

    def devices(self) -> List[str]:
        """
        Retrieves a list of all AWS Braket devices (backends) provided through PLANQK that can be accessed using this SDK.

        Returns:
            List[str]: A list of supported AWS Braket device IDs.
        """
        return list(self._device_mapping.keys())

    def _get_backend_info(self, backend_id):
        try:
            return self._client.get_backend(backend_id=backend_id)
        except PlanqkClientError as e:
            if e.response.status_code == 404:
                raise BackendNotFoundError(f"PLANQK device with id {backend_id} not found.")
            raise e

    def _get_planqk_braket_device(self, backend_info: BackendDto) -> PlanqkAwsDevice:
        device_class = self.get_device_class(backend_info.id)
        return device_class(planqk_client=self._client, backend_info=backend_info)
