"""
Backward compatibility module for planqk.qiskit imports.
This module provides access to the quantum providers for existing code.
"""

from planqk.quantum.sdk.qiskit.backend import PlanqkQiskitBackend
from planqk.quantum.sdk.qiskit.job import PlanqkQiskitJob
# Import from the new quantum structure for backward compatibility
from planqk.quantum.sdk.qiskit.provider import PlanqkQuantumProvider

# Re-export for backward compatibility
__all__ = ['PlanqkQuantumProvider', 'PlanqkQiskitBackend', 'PlanqkQiskitJob']
