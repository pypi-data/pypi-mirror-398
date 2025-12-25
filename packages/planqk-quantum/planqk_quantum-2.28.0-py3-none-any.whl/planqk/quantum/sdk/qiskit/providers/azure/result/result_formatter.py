from abc import ABC, abstractmethod
from typing import List, Dict, Any

from planqk.quantum.sdk.qiskit import PlanqkQiskitJob


class ResultFormatter(ABC):

    def __init__(self, results: any, job: PlanqkQiskitJob):
        self.results = results
        self.job = job

    @abstractmethod
    def format_result(self) -> List[Dict[str, Any]]:
        pass
