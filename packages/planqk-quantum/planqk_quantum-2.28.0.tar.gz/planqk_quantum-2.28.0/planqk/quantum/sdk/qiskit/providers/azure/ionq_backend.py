from qiskit import QuantumCircuit
from qiskit_ionq.helpers import qiskit_circ_to_ionq_circ

from planqk.quantum.sdk.client.model_enums import JobInputFormat
from planqk.quantum.sdk.qiskit.options import OptionsV2
from planqk.quantum.sdk.qiskit.provider import PlanqkQuantumProvider
from planqk.quantum.sdk.qiskit.providers.azure.azure_backend import PlanqkAzureQiskitBackend


@PlanqkQuantumProvider.register_backend("azure.ionq.simulator")
class PlanqkAzureIonqBackend(PlanqkAzureQiskitBackend):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def _default_options(cls):
        return OptionsV2(
            shots=500
        )

    def _convert_to_job_input(self, job_input, options=None):
        gateset = options.get("gateset", "qis")
        ionq_circ, _, _ = qiskit_circ_to_ionq_circ(job_input, gateset=gateset)
        return {
            "gateset": gateset,
            "qubits": job_input.num_qubits,
            "circuit": ionq_circ,
        }

    def _get_job_input_format(self) -> JobInputFormat:
        return JobInputFormat.IONQ_CIRCUIT_V1

    def _convert_to_job_params(self, job_input: QuantumCircuit = None, options=None) -> dict:
        memory_option = options.get("memory", None)
        return {"memory": memory_option} if memory_option is not None else {}
