"""Factory for creating BackendInfo instances with provider support detection."""
from planqk.quantum.sdk.client.backend_dtos import BackendDto, BackendInfo
from planqk.quantum.sdk.client.model_enums import Provider


class BackendInfoFactory:
    """Factory for creating BackendInfo instances from BackendDto objects.

    This factory centralizes the logic for creating BackendInfo instances,
    including detection of which providers support each backend. It uses lazy
    imports to avoid circular dependencies between providers.

    Example:
        >>> from planqk.quantum.sdk.client import BackendInfoFactory
        >>> backend_dto = client.get_backend("aws.ionq.aria")
        >>> info = BackendInfoFactory.from_backend_dto(backend_dto)
        >>> print(info.supported_providers)
        {'PlanqkQuantumProvider', 'PlanqkBraketProvider'}
    """

    @staticmethod
    def from_backend_dto(backend_dto: BackendDto) -> BackendInfo:
        """Create a BackendInfo instance from a BackendDto.

        This method creates a BackendInfo object and automatically detects
        which providers (PlanqkQuantumProvider, PlanqkBraketProvider,
        PlanqkQiskitRuntimeService) support the given backend.

        Args:
            backend_dto: The backend data transfer object from the PLANQK API.

        Returns:
            BackendInfo with provider support information populated.
        """
        supported_providers = BackendInfoFactory._detect_supported_providers(
            backend_dto.id, backend_dto.provider
        )

        return BackendInfo(
            id=backend_dto.id,
            provider=backend_dto.provider,
            hardware_provider=backend_dto.hardware_provider,
            type=backend_dto.type,
            supported_providers=supported_providers
        )

    @staticmethod
    def _detect_supported_providers(backend_id: str, provider: Provider) -> set:
        """Detect which providers support a given backend.

        Uses lazy imports to check each provider's backend/device mapping
        without causing circular import issues.

        Args:
            backend_id: The backend identifier (e.g., 'aws.ionq.aria').
            provider: The cloud provider enum value.

        Returns:
            Set of provider class names that support this backend. Possible values:
            - 'PlanqkQuantumProvider': Qiskit-based provider for most backends
            - 'PlanqkBraketProvider': Amazon Braket provider for AWS devices
            - 'PlanqkQiskitRuntimeService': IBM Qiskit Runtime for IBM backends
        """
        supported_providers = set()

        # Check PlanqkQuantumProvider support (Qiskit backends)
        try:
            from planqk.quantum.sdk.qiskit.provider import PlanqkQuantumProvider
            if backend_id in PlanqkQuantumProvider._backend_mapping:
                supported_providers.add("PlanqkQuantumProvider")
        except ImportError:
            pass

        # Check PlanqkBraketProvider support (AWS Braket devices)
        try:
            from planqk.quantum.sdk.braket.braket_provider import PlanqkBraketProvider
            if backend_id in PlanqkBraketProvider._device_mapping:
                supported_providers.add("PlanqkBraketProvider")
        except ImportError:
            pass

        # Check PlanqkQiskitRuntimeService support (IBM backends only)
        if provider == Provider.IBM:
            try:
                from planqk.quantum.sdk.qiskit.planqk_qiskit_runtime_service import PlanqkQiskitRuntimeService
                if backend_id in PlanqkQiskitRuntimeService._backend_mapping:
                    supported_providers.add("PlanqkQiskitRuntimeService")
            except ImportError:
                pass

        return supported_providers
