import sys
if sys.version_info < (3, 11):
    raise RuntimeError(
        f"PLANQK SDK requires Python 3.11 or higher; "
        f"you are running {sys.version_info.major}.{sys.version_info.minor}."
    )


"""
PLANQK Quantum SDK module providing unified access to quantum providers.
"""

from ._version import __version__

from .client.backend_dtos import BackendDto, BackendStateInfosDto
from .client.job_dtos import JobDto
from .client.model_enums import Provider, JobInputFormat, PlanqkSdkProvider
from .client.client import _PlanqkClient

# Type annotations for IDE support
from typing import Type

PlanqkQuantumProvider: Type['PlanqkQuantumProvider']
PlanqkBraketProvider: Type['PlanqkBraketProvider']
PlanqkQiskitRuntimeService: Type['PlanqkQiskitRuntimeService']

# Submodules will be available via lazy loading

__all__ = [
    'PlanqkQuantumProvider',
    'PlanqkBraketProvider',
    'PlanqkQiskitRuntimeService',

    '__version__',
    'braket', 'qiskit', 'client'
]


def __getattr__(name: str):
    import sys
    current_module = sys.modules[__name__]

    if name == "PlanqkBraketProvider":
        from .braket.braket_provider import PlanqkBraketProvider
        setattr(current_module, name, PlanqkBraketProvider)
        return PlanqkBraketProvider
    elif name == "PlanqkQuantumProvider":
        from .qiskit.provider import PlanqkQuantumProvider
        setattr(current_module, name, PlanqkQuantumProvider)
        return PlanqkQuantumProvider
    elif name == "PlanqkQiskitRuntimeService":
        from planqk.quantum.sdk.qiskit.planqk_qiskit_runtime_service import PlanqkQiskitRuntimeService
        setattr(current_module, name, PlanqkQiskitRuntimeService)
        return PlanqkQiskitRuntimeService
    elif name == "braket":
        from . import braket
        setattr(current_module, name, braket)
        return braket
    elif name == "qiskit":
        from . import qiskit
        setattr(current_module, name, qiskit)
        return qiskit
    elif name == "client":
        from . import client
        setattr(current_module, name, client)
        return client
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

