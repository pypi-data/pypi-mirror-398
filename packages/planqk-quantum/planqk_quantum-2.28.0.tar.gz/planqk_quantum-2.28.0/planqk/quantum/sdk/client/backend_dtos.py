from dataclasses import dataclass, field
from datetime import time, date
from typing import Dict, Set
from typing import List
from typing import Optional

from pydantic import BaseModel, field_validator

from planqk.quantum.sdk.client.dto_utils import init_with_defined_params
from planqk.quantum.sdk.client.model_enums import Provider, BackendType, HardwareProvider, PlanqkBackendStatus, JobInputFormat


@dataclass
class BackendInfo:
    """Information about a quantum backend including SDK support.

    This class provides detailed information about a backend, including
    which SDKs can be used to access it.

    Attributes:
        id: The unique backend identifier (e.g., 'aws.ionq.aria').
        provider: The cloud provider (e.g., Provider.AWS, Provider.AZURE).
        hardware_provider: The hardware manufacturer (e.g., HardwareProvider.IONQ).
        type: The backend type (BackendType.QPU or BackendType.SIMULATOR).
        supported_providers: Set of provider class names that can access this backend.
            Possible values: 'PlanqkQuantumProvider', 'PlanqkBraketProvider',
            'PlanqkQiskitRuntimeService'.

    Example:
        >>> info = BackendInfo(
        ...     id="aws.ionq.aria",
        ...     provider=Provider.AWS,
        ...     hardware_provider=HardwareProvider.IONQ,
        ...     type=BackendType.QPU,
        ...     supported_providers={"PlanqkQuantumProvider", "PlanqkBraketProvider"}
        ... )
        >>> info.supports_provider("PlanqkBraketProvider")
        True
    """
    id: str
    provider: Provider
    hardware_provider: Optional[HardwareProvider] = None
    type: Optional[BackendType] = None
    supported_providers: Set[str] = field(default_factory=set)

    def supports_provider(self, provider_name: str) -> bool:
        """Check if this backend can be accessed by the given provider.

        Args:
            provider_name: The name of the provider class (e.g., 'PlanqkQuantumProvider').

        Returns:
            True if the backend can be accessed by the specified provider, False otherwise.
        """
        return provider_name in self.supported_providers


class DocumentationDto(BaseModel):
    description: Optional[str] = None
    url: Optional[str] = None
    # status_url: Optional[str] = None
    location: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict):
        return init_with_defined_params(cls, data)


class QubitDto(BaseModel):
    id: str

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**data)


class GateDto(BaseModel):
    name: str
    native_gate: bool

    @classmethod
    def from_dict(cls, data: Dict):
        return init_with_defined_params(cls, data)


class ConnectivityDto(BaseModel):
    fully_connected: bool
    graph: Optional[Dict[str, List[str]]] = None

    @classmethod
    def from_dict(cls, data: Dict):
        return init_with_defined_params(cls, data)


class ShotsRangeDto(BaseModel):
    min: int
    max: int

    @classmethod
    def from_dict(cls, data: Dict):
        return init_with_defined_params(cls, data)


class ConfigurationDto(BaseModel):
    gates: List[GateDto]
    instructions: List[str]
    qubits: Optional[List[QubitDto]] = None
    qubit_count: int
    connectivity: Optional[ConnectivityDto] = None
    supported_input_formats: List[JobInputFormat]
    shots_range: ShotsRangeDto
    memory_result_supported: Optional[bool] = False
    options: Optional[Dict] = None

    @field_validator('supported_input_formats', mode='before')
    def _validate_supported_input_formats(cls, v):
        if v is None:
            return []
        return [JobInputFormat.from_str(format_str) for format_str in v]

    def __post_init__(self):
        self.gates = [GateDto.from_dict(gate) for gate in self.gates]
        self.qubits = [QubitDto.from_dict(qubit) for qubit in self.qubits]
        self.connectivity = ConnectivityDto.from_dict(self.connectivity)
        self.shots_range = ShotsRangeDto.from_dict(self.shots_range)

    @classmethod
    def from_dict(cls, data: Dict):
        return init_with_defined_params(cls, data)


class AvailabilityTimesDto(BaseModel):
    granularity: str
    start: time
    end: time

    @classmethod
    def from_dict(cls, data: Dict):
        return init_with_defined_params(cls, data)


class CostDto(BaseModel):
    granularity: str
    currency: str
    value: float

    @classmethod
    def from_dict(cls, data: Dict):
        return init_with_defined_params(cls, data)


class BackendStateInfosDto(BaseModel):
    status: PlanqkBackendStatus
    queue_avg_time: Optional[int] = None
    queue_size: Optional[int] = None
    provider_token_valid: Optional[bool] = None

    def __post_init__(self):
        self.status = PlanqkBackendStatus(self.status) if self.status else None

    @classmethod
    def from_dict(cls, data: Dict):
        return init_with_defined_params(cls, data)


class BackendDto(BaseModel):
    id: str
    provider: Provider

    @field_validator('provider', mode='before')
    def _validate_provider(cls, v):
        return Provider.from_str(v)

    internal_id: Optional[str] = None
    hardware_provider: Optional[HardwareProvider] = None

    @field_validator('hardware_provider', mode='before')
    def _validate_hardware_provider(cls, v):
        return HardwareProvider.from_str(v)

    name: Optional[str] = None
    documentation: Optional[DocumentationDto] = None
    configuration: Optional[ConfigurationDto] = None
    type: Optional[BackendType] = None
    status: Optional[PlanqkBackendStatus] = None
    availability: Optional[List[AvailabilityTimesDto]] = None
    costs: Optional[List[CostDto]] = None
    updated_at: Optional[date] = None
    avg_queue_time: Optional[int] = None
