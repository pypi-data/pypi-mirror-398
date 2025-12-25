from typing import Dict, List, Optional, Union

from qiskit.providers import Backend
from qiskit.result import Counts, Result
from qiskit.result.models import ExperimentResult, ExperimentResultData

from planqk.quantum.sdk import JobDto
from planqk.quantum.sdk.client import PlanqkJobStatus
from planqk.quantum.sdk.client.model_enums import PLANQK_JOB_FINAL_STATES
from planqk.quantum.sdk.qiskit import PlanqkQiskitJob
from planqk.quantum.sdk.qiskit.providers.iqm.planqk_iqm_client import _PlanqkIqmClient


class PlanqkIqmQiskitJob(PlanqkQiskitJob):

    def __init__(self, backend: Optional[Backend], job_id: Optional[str] = None, job_details: Optional[JobDto] = None,
                 planqk_client: Optional[_PlanqkIqmClient] = None):
        super().__init__(backend, job_id, job_details, planqk_client)

    def _result_states(self) -> set[PlanqkJobStatus]:
        return PLANQK_JOB_FINAL_STATES

    def _create_experiment_result(self, provider_result: dict) -> ExperimentResult:
        """Transform IQM measurement results to Qiskit ExperimentResult format.

        Args:
            provider_result: IQM measurement results containing counts and metadata

        Returns:
            ExperimentResult with counts and memory data from first measurement batch
        """
        result = self.iqm_to_experiment_result(provider_result)
        if result.results:
            return result.results[0]
        else:
            # Return empty ExperimentResult if no results
            return ExperimentResult(
                shots=0,
                success=True,
                data=ExperimentResultData(counts={})
            )

    def iqm_to_experiment_result(self,
            iqm_meas_results: List[Dict[str, Union[List[str], Dict[str, int]]]],
    ) -> Result:
        """
        Convert IQM-style measurement results into a Qiskit Result.

        Args:
            iqm_meas_results: List of measurement result dicts. Each dict contains
                            'measurement_keys' and 'counts' keys.

        Returns:
            A qiskit.result.Result containing the converted measurement results.
        """
        if not iqm_meas_results:
            # Return empty result if no data
            return Result(
                backend_name=self._backend.name if self._backend else "unknown",
                backend_version="1.0",
                job_id=self._job_id,
                qobj_id=0,
                success=True,
                results=[],
                status="COMPLETED",
                date=None,
            )

        # Convert each IQM measurement result to a Qiskit ExperimentResult
        experiment_results = []
        for i, measurement_batch in enumerate(iqm_meas_results):
            counts_dict = measurement_batch.get("counts", {})
            # Calculate total shots from counts
            total_shots = sum(counts_dict.values())

            # Create memory data by expanding counts into individual shot results
            memory = []
            for state, count in counts_dict.items():
                memory.extend([state] * count)

            experiment_result = {
                "shots": total_shots,
                "success": True,
                "data": {
                    "memory": memory,
                    "counts": Counts(counts_dict),
                },
                "header": {"name": f"circ{i}"},
                "status": "DONE",
            }
            experiment_results.append(experiment_result)

        result_dict = {
            "backend_name": self._backend.name if self._backend else "unknown",
            "backend_version": "1.0",
            "qobj_id": 0,
            "job_id": self._job_id,
            "success": True,
            "results": experiment_results,
            "date": None,
        }
        return Result.from_dict(result_dict)