from __future__ import annotations

import json
from typing import Any, Union, Optional

from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation
from braket.annealing.problem import Problem
from braket.aws import AwsQuantumTask
from braket.aws.aws_session import AwsSession
from braket.aws.queue_information import QuantumTaskQueueInfo
from braket.circuits.circuit import Circuit, Gate, QubitSet
from braket.ir.blackbird import Program as BlackbirdProgram
from braket.ir.openqasm import Program as OpenQASMProgram
from braket.pulse.pulse_sequence import PulseSequence
from braket.schema_common import BraketSchemaBase
from braket.tasks import AnalogHamiltonianSimulationQuantumTaskResult, GateModelQuantumTaskResult

from planqk.quantum.sdk.client.client import _PlanqkClient
from planqk.quantum.sdk.client.job_dtos import JobDto
from planqk.quantum.sdk.client.model_enums import PlanqkJobStatus
from planqk.quantum.sdk.decorators import not_implemented
from planqk.quantum.sdk.exceptions import PlanqkError
from planqk.quantum.sdk.job import PlanqkBaseJob


class PlanqkAwsQuantumTask(PlanqkBaseJob, AwsQuantumTask):

    def __init__(self,
                 task_id: Optional[str] = None,
                 access_token: Optional[str] = None,
                 organization_id: Optional[str] = None,
                 _job_details: Optional[JobDto] = None,
                 _backend: Optional = None,
                 _client: _PlanqkClient = None):
        """
        Initialize the PlanqkAwsQuantumTask.

        Args:
            task_id (str, optional):
                The unique identifier of the quantum task. This ID is used to reference an existing task on PLANQK,
                allowing the task's status, results, and other details to be retrieved or managed.
                Defaults to None.

            access_token (str, optional):
                Access token used for authentication with PLANQK. If no token is provided, the token is retrieved
                from the environment variable `PLANQK_ACCESS_TOKEN`, which can be set manually or by using the
                PLANQK CLI. This token is used to authorize access to PLANQK services. Defaults to None.

            organization_id (str, optional):
                The ID of a PLANQK organization you are a member of. Provide this ID if you want to access
                quantum backends with an organization account and its associated pricing plan. All backend
                executions (jobs, tasks, etc.) you create are visible to the members of the organization.
                If the ID is omitted, all backend executions are performed under your personal account.
                Defaults to None.

            _job_details (JobDto, optional):
                Internal use only. Contains detailed information about the details associated with this task,
                including metadata such as name, status, and configuration details relevant to the task.
                Defaults to None.

            _backend (optional):
                Internal use only. Specifies the backend on which the quantum task is executed.
                Defaults to None.

            _client (_PlanqkClient, optional):
                Internal use only. A client instance used for making requests to the PLANQK API. This parameter is
                mainly intended for testing purposes.
                Defaults to None.

         Raises:
            BackendNotFoundError: If the device where the task was executed on cannot be found or is not supported by the Braket SDK.
        """
        client = _client or _PlanqkClient(access_token=access_token, organization_id=organization_id)
        PlanqkBaseJob.__init__(self, backend=_backend, job_id=task_id, job_details=_job_details, planqk_client=client)

        is_existing_task = task_id is not None
        if is_existing_task:
            self._verify_task_device_is_supported()

    def _verify_task_device_is_supported(self):
        from planqk.quantum.sdk.braket  import PlanqkBraketProvider
        backend_id = self._job_details.backend_id
        PlanqkBraketProvider.get_device_class(backend_id)

    @staticmethod
    @not_implemented
    def create(
        aws_session: AwsSession,
        device_arn: str,
        task_specification: Union[
            Circuit,
            Problem,
            OpenQASMProgram,
            BlackbirdProgram,
            PulseSequence,
            AnalogHamiltonianSimulation,
        ],
        s3_destination_folder: AwsSession.S3DestinationFolder,
        shots: int,
        device_parameters: dict[str, Any] | None = None,
        disable_qubit_rewiring: bool = False,
        tags: dict[str, str] | None = None,
        inputs: dict[str, float] | None = None,
        gate_definitions: dict[tuple[Gate, QubitSet], PulseSequence] | None = None,
        quiet: bool = False,
        reservation_arn: str | None = None,
        *args,
        **kwargs,
    ) -> AwsQuantumTask:
        # Task must be either created with PlanqkAwsDevice.run() or retrieved by specifying the task ID in the constructor of the PlanqkAwsQuantumTask class.
        pass

    @not_implemented
    def metadata(self, use_cached_value: bool = False) -> dict[str, Any]:
        """Get quantum task metadata defined in Amazon Braket.

        Args:
            use_cached_value (bool): If `True`, uses the value most recently retrieved
                from the Amazon Braket `GetQuantumTask` operation, if it exists; if not,
                `GetQuantumTask` will be called to retrieve the metadata. If `False`, always calls
                `GetQuantumTask`, which also updates the cached value. Default: `False`.

        Returns:
            dict[str, Any]: The response from the Amazon Braket `GetQuantumTask` operation.
            If `use_cached_value` is `True`, Amazon Braket is not called and the most recently
            retrieved value is used, unless `GetQuantumTask` was never called, in which case
            it will still be called to populate the metadata for the first time.
        """
        pass

    def state(self, use_cached_value: bool = False) -> str:
        """The state of the quantum task.

        Args:
            use_cached_value (bool): If `True`, uses the value most recently retrieved from PLANQK.

        Returns:
            str: the job execution state.
        """
        state = PlanqkBaseJob._update_state(self, use_cached_value)
        return 'QUEUED' if state == PlanqkJobStatus.PENDING else state.value

    @not_implemented
    def queue_position(self) -> QuantumTaskQueueInfo:
        """The queue position details for the quantum task."""
        pass

    @property
    def id(self) -> str:
        """Get the quantum task ID.

        Returns:
            str: The quantum task ID.
        """
        return super().id

    def job_id(self) -> str:
        """Get the quantum task ID.

        Returns:
            str: The quantum task ID.
        """
        return self.id

    def cancel(self) -> None:
        """Cancel the quantum task."""
        super().cancel()

    @not_implemented
    def async_result(self):
        """Get the quantum task result asynchronously.

        Returns:
            asyncio.Task: Get the quantum task result asynchronously.
        """
        pass

    def result(
        self,
    ) -> Union[AnalogHamiltonianSimulationQuantumTaskResult, GateModelQuantumTaskResult]:
        """Retrieve the quantum task result by polling PLANQK until the task is completed.

        Returns:
            Union[AnalogHamiltonianSimulationQuantumTaskResult, GateModelQuantumTaskResult]:
                An instance of `AnalogHamiltonianSimulationQuantumTaskResult` if the task was executed on an Analog Hamiltonian Simulator
                or an instance of `GateModelQuantumTaskResult` if the task was performed on a Gate-based device.
        Raises:
            PlanqkError: If the AWS task result type is unexpected or unrecognized.
        """
        try:
            result = super()._result()
            result_type = result.get('braketSchemaHeader', {}).get('name')
            if result_type == "braket.task_result.analog_hamiltonian_simulation_task_result":
                return AnalogHamiltonianSimulationQuantumTaskResult.from_string(json.dumps(result))

            elif result_type == "braket.task_result.gate_model_task_result":
                gate_model_result = BraketSchemaBase.parse_raw_schema(json.dumps(result))
                GateModelQuantumTaskResult.cast_result_types(gate_model_result)
                return GateModelQuantumTaskResult.from_object(gate_model_result)
            else:
                raise ValueError(f"Unexpected AWS task result type '{result_type}'")
        except Exception as e:
            raise PlanqkError(f"Cannot process AWS task result {result}: {e}") from e
