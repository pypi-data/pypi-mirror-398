from __future__ import annotations

from abc import abstractmethod, ABC
from copy import copy
from typing import Union, Optional, Dict, Any, TYPE_CHECKING

from braket.ahs import AnalogHamiltonianSimulation
from braket.circuits import Circuit
from qiskit import QuantumCircuit

from planqk.quantum.sdk.client.backend_dtos import BackendDto, BackendStateInfosDto
from planqk.quantum.sdk.client.client import _PlanqkClient
from planqk.quantum.sdk.client.job_dtos import JobDto
from planqk.quantum.sdk.client.model_enums import Provider, JobInputFormat, PlanqkSdkProvider
from planqk.quantum.sdk.job import PlanqkBaseJob

if TYPE_CHECKING:
    from planqk.quantum.sdk.qiskit.job import PlanqkQiskitJob
    from planqk.quantum.sdk.braket import PlanqkAwsQuantumTask


class PlanqkBackend(ABC):
    def __init__(  # pylint: disable=too-many-arguments
            self,
            backend_info: BackendDto,
            planqk_client: _PlanqkClient,
    ):
        """PlanqkBackend for executing inputs against PLANQK devices.

        Example:
            provider = PlanqkQuantumProvider()
            backend = provider.get_backend("azure.ionq.simulator")
            input = ... # Can be Qiskit circuit
            backend.run(input, shots=10).result().get_counts()
            {"100": 10, "001": 10}

        Args:
            backend_info: PLANQK actual infos
            provider: Qiskit provider for this actual
            name: name of actual
            description: description of actual
            online_date: online date
            backend_version: actual version
            **fields: other arguments
        """

        self._planqk_client = planqk_client
        if self._planqk_client is None:
            raise RuntimeError("planqk_client must not be None")

        self._backend_info = backend_info

    @property
    def backend_info(self) -> BackendDto:
        return self._backend_info

    @property
    def min_shots(self):
        return self.backend_info.configuration.shots_range.min

    @property
    def max_shots(self):
        return self.backend_info.configuration.shots_range.max

    def calibration(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve the currently effective calibration data of the backend.

        Note: Backend calibrations are unavailable for simulators.

        Returns:
            Optional[Dict[str, Any]]: Backend calibration data or None if no calibration data is available.
            The data format is backend specific.
        """
        return self._planqk_client.get_backend_calibration(self.backend_info.id)

    def run(self, job_input: Union[QuantumCircuit, Circuit, AnalogHamiltonianSimulation], shots: Optional[int] = None,
            sdk_provider: PlanqkSdkProvider = None,
            **kwargs: object) -> Union[PlanqkQiskitJob, PlanqkAwsQuantumTask]:
        """Runs an experiment on the backend as job.

        Args:
            job_input (QuantumCircuit, AnalogHamiltonianSimulation): job input to run, e.g. a Qiskit circuit or a hamiltonian. Currently only a single input can be executed per job.
            shots (int): the number of shots
            sdk_provider (PlanqkSdkProvider): the SDK provider used for the execution
            **kwargs: additional arguments for the execution
        Returns:
            The job object representing the experiment
        """

        if isinstance(job_input, (list, tuple)):
            if len(job_input) > 1:
                raise ValueError("Multi-experiment jobs are not supported")
            job_input = job_input[0]

        # add kwargs, if defined as options, to a copy of the options
        options = {}
        if hasattr(self, 'options'):
            options = copy(self.options)

        if kwargs:
            for field in kwargs:
                if field in options.data:
                    options[field] = kwargs[field]

        shots = shots if shots else self.backend_info.configuration.shots_range.min
        options['shots'] = shots
        job_input_format = self._get_job_input_format()
        converted_job_input = self._convert_to_job_input(job_input, options)
        input_params = self._convert_to_job_params(job_input, options)

        job_request = JobDto(backend_id=self.backend_info.id,
                             provider=self.backend_info.provider.name,
                             input_format=job_input_format,
                             input=converted_job_input,
                             shots=shots,
                             sdk_provider=sdk_provider,
                             input_params=input_params,
                             name=kwargs.get('name', None))

        return self._run_job(job_request)

    @abstractmethod
    def _convert_to_job_input(self, job_input: Union[QuantumCircuit, AnalogHamiltonianSimulation], options=None) -> dict:
        pass

    def _convert_to_job_params(self, job_input: QuantumCircuit = None, options=None) -> dict:
        return {}

    @abstractmethod
    def _get_job_input_format(self) -> JobInputFormat:
        pass

    @abstractmethod
    def _run_job(self, job_request: JobDto) -> PlanqkBaseJob:
        pass

    @property
    def backend_provider(self) -> Provider:
        """Return the provider offering the quantum backend resource."""
        return self.backend_info.provider

    def _get_backend_config(self, refresh: bool = False) -> Dict[str, Any]:
        backend_config = getattr(self, "_backend_config", None)
        if backend_config is None or refresh:
            self._backend_config = self._planqk_client.get_backend_config(self.backend_info.id)
        return self._backend_config

    def _get_backend_state(self) -> BackendStateInfosDto:
        return self._planqk_client.get_backend_state(self.backend_info.id)