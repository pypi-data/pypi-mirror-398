import random
from collections import defaultdict

import numpy as np
from qiskit.providers import JobStatus
from qiskit.result.models import ExperimentResult

from planqk.quantum.sdk.qiskit import PlanqkQiskitJob
from planqk.quantum.sdk.qiskit.providers.azure.result.result_formatter import ResultFormatter


class IonqResultFormatter(ResultFormatter):
    """
       Transform the Azure IonQ results to Qiskit result format.

       Adapted from Azure Quantum Qiskit SDK's job.py module.

       Original source:
       Azure Quantum SDK (MIT License)
       GitHub Repository: https://github.com/microsoft/azure-quantum-python/blob/main/azure-quantum/azure/quantum/qiskit/job.py
    """

    def __init__(self, results: any, job: PlanqkQiskitJob):
        super().__init__(results, job)

    def format_result(self) -> ExperimentResult:
        job_result = {"data": self._format_ionq_results(),
                      "success": True,
                      "header": {},
                      "status": JobStatus.DONE.name,
                      "shots": self.job.shots}

        return ExperimentResult.from_dict(job_result)

    def _format_ionq_results(self) -> dict:
        result = self.results
        job = self.job
        job_details = job._job_details
        num_qubits_str = job_details.input_params.get("qubits")
        if not num_qubits_str:
            raise KeyError(f"Job {job.job_id()} does not have the required metadata (qubits) to format IonQ results.")

        num_qubits = int(num_qubits_str)

        if 'histogram' not in result:
            raise KeyError("Histogram missing in IonQ Job results")

        probabilities = defaultdict(int)
        for key, value in result['histogram'].items():
            bitstring = self._to_bitstring(key, num_qubits)
            probabilities[bitstring] += value

        if job.backend().configuration().simulator:
            counts = self._draw_random_sample(probabilities, job.shots)
        else:
            counts = {bitstring: int(np.round(self.shots * value)) for bitstring, value in probabilities.items()}

        job_details.input_params.get("memory")

        memory = []
        memory_param = job_details.input_params.get("memory")
        if memory_param:
            # Azure Ionq simulator does not support memory natively, hence, it is randomly created. Memory is required for supporting pennylane
            memory = self._generate_random_memory(counts, self.job.shots)

        return {"counts": counts, "probabilities": probabilities, "memory": memory}

    @staticmethod
    def _to_bitstring(k: str, num_qubits):
        # flip bitstring to convert to little Endian
        return format(int(k), f"0{num_qubits}b")[::-1]

    def _draw_random_sample(self, probabilities, shots):
        _norm = sum(probabilities.values())
        if _norm != 1:
            if np.isclose(_norm, 1.0, rtol=1e-2):
                probabilities = {k: v / _norm for k, v in probabilities.items()}
            else:
                raise ValueError(f"Probabilities do not add up to 1: {probabilities}")

        import hashlib
        job_id = self.job.job_id()
        sampler_seed = int(hashlib.sha256(job_id.encode('utf-8')).hexdigest(), 16) % (2 ** 32 - 1)

        rng = np.random.default_rng(sampler_seed)
        rand_values = rng.choice(list(probabilities.keys()), shots, p=list(probabilities.values()))
        unique, counts = np.unique(rand_values, return_counts=True)
        return {str(k): int(v) for k, v in zip(unique, counts)}

    @staticmethod
    def _generate_random_memory(counts: dict, shots: int):
        return random.choices(list(counts.keys()), weights=counts.values(), k=shots)
