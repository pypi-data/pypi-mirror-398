from enum import Enum


class Provider(Enum):
    AZURE = "AZURE"
    AWS = "AWS"
    DWAVE = "DWAVE"
    IBM = "IBM"
    IBM_CLOUD = "IBM_CLOUD"
    TSYSTEMS = "TSYSTEMS"
    QRYD = "QRYD"
    QUDORA = "QUDORA"
    IQM = "IQM"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def from_str(cls, provider_str):
        try:
            return Provider(provider_str)
        except ValueError:
            return cls.UNKNOWN


class BackendType(Enum):
    QPU = "QPU"
    SIMULATOR = "SIMULATOR"
    ANNEALER = "ANNEALER"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def from_str(cls, type_str):
        try:
            return BackendType(type_str)
        except ValueError:
            return cls.UNKNOWN


class HardwareProvider(Enum):
    IONQ = "IONQ"
    RIGETTI = "RIGETTI"
    OQC = "OQC"
    AWS = "AWS"
    AZURE = "AZURE"
    IBM = "IBM"
    QRYD = "QRYD"
    DWAVE = "DWAVE"
    QUERA = "QUERA"
    IQM = "IQM"
    QUDORA = "QUDORA"
    QUANTINUUM = "QUANTINUUM"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def from_str(cls, hw_provider_str):
        try:
            return HardwareProvider(hw_provider_str)
        except ValueError:
            return cls.UNKNOWN


class PlanqkBackendStatus(Enum):
    """
    STATUS Enum:

    UNKNOWN: The actual status is unknown.
    ONLINE: The actual is online, processing submitted jobs and accepting new ones.
    PAUSED: The actual is accepting jobs, but not currently processing them.
    OFFLINE: The actual is not accepting new jobs, e.g. due to maintenance.
    RETIRED: The actual is not available for use anymore.
    """
    UNKNOWN = "UNKNOWN"
    ONLINE = "ONLINE"
    PAUSED = "PAUSED"
    OFFLINE = "OFFLINE"
    RETIRED = "RETIRED"

    @classmethod
    def from_str(cls, status_str):
        try:
            return PlanqkBackendStatus(status_str)
        except ValueError:
            return cls.UNKNOWN


class PlanqkSdkProvider(Enum):
    QISKIT = "QISKIT"
    BRAKET = "BRAKET"
    CLIENT = "CLIENT"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def from_str(cls, provider_str):
        try:
            return PlanqkSdkProvider(provider_str)
        except ValueError:
            return cls.UNKNOWN


class PlanqkJobStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    ABORTED = "ABORTED"
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLING = "CANCELLING"
    CANCELLED = "CANCELLED"

    @classmethod
    def from_str(cls, job_status_str):
        try:
            return PlanqkJobStatus(job_status_str.upper())
        except ValueError:
            return cls.UNKNOWN


PLANQK_JOB_FINAL_STATES = (PlanqkJobStatus.ABORTED, PlanqkJobStatus.COMPLETED, PlanqkJobStatus.CANCELLED, PlanqkJobStatus.FAILED)


class JobInputFormat(str, Enum):
    OPEN_QASM_V1 = "OPEN_QASM_V1"
    OPEN_QASM_V2 = "OPEN_QASM_V2"
    OPEN_QASM_V3 = "OPEN_QASM_V3"
    QIR_V1 = "QIR_V1"
    BRAKET_OPEN_QASM_V3 = "BRAKET_OPEN_QASM_V3"
    BRAKET_AHS_PROGRAM = "BRAKET_AHS_PROGRAM"
    IONQ_CIRCUIT_V1 = "IONQ_CIRCUIT_V1"
    IQM_JOB_INPUT_V1 = "IQM_JOB_INPUT_V1"
    QISKIT = "QISKIT"
    QISKIT_QPY = "QISKIT_QPY"
    QOQO = "QOQO"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def from_str(cls, job_input_format_str):
        try:
            return JobInputFormat(job_input_format_str)
        except ValueError:
            return cls.UNKNOWN
