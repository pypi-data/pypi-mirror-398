from typing import Optional
from uuid import UUID

from qiskit import QuantumCircuit
from qiskit.providers import Options
from qiskit.transpiler import Target

from planqk.quantum.sdk.qiskit.backend import PlanqkQiskitBackend
from planqk.quantum.sdk.qiskit.provider import PlanqkQuantumProvider
from planqk.quantum.sdk.client.backend_dtos import BackendDto
from planqk.quantum.sdk.client.client import _PlanqkClient
from planqk.quantum.sdk.client.model_enums import Provider, JobInputFormat
from planqk.quantum.sdk.qiskit.providers.iqm.iqm_client_sdk.qiskit_iqm.iqm_provider import IQMBackend
from planqk.quantum.sdk.qiskit.providers.iqm.planqk_iqm_client import _PlanqkIqmClient


@PlanqkQuantumProvider.register_backend("iqm.qpu.emerald")
class PlanqkIqmEmeraldBackend(PlanqkQiskitBackend):
    """PLANQK wrapper backend for IQM Emerald QPU.

    Acts as an adapter that wraps the native IQMBackend from the IQM SDK,
    routing PLANQK platform requests through _PlanqkIqmClient to the underlying
    IQM backend implementation while maintaining PLANQK integration.
    """
    def __init__(self, planqk_client: _PlanqkClient, backend_info: BackendDto):
        backend_id = backend_info.id
        self._backend = backend_info
        self._planqk_iqm_client = _PlanqkIqmClient(planqk_client, backend_id)
        self._iqm_backend = self._get_backend(name=backend_id)
        super().__init__(planqk_client, backend_info)

    def _get_backend(
            self, name: str | None = None, calibration_set_id: UUID | None = None
    ) -> IQMBackend:
        """Creates and returns the wrapped IQM backend instance using _PlanqkIqmClient as adapter."""

        if name and name.startswith("facade_"):
            raise NotImplementedError("Access to facade backends is not yet implemented. "
                                      " Please contact PLANQK support if you require this functionality.")

        return IQMBackend(self._planqk_iqm_client, calibration_set_id=calibration_set_id)

    def _planqk_backend_to_target(self) -> Target:
        """Returns target from wrapped IQM backend, delegating to native IQM implementation."""
        return self._iqm_backend.target

    def _initialize_backend_components(self):
        """Initialize backend using wrapped IQM backend's target.

        IQM backend delegates target management to the vendored IQM SDK's
        IQMBackend, which constructs the target from IQM's dynamic quantum
        architecture (DQA). This overrides the parent's initialization to
        prevent calling abstract methods that aren't needed for IQM.
        """
        # Use pre-built target from wrapped IQM backend
        self._target = self._iqm_backend.target
        # IQM doesn't use QasmBackendConfiguration
        self._configuration = None

    def _to_gate(self, name: str):
        """Not implemented - gate conversion handled by wrapped IQMBackend.

        This method is required by parent class but not called due to
        _initialize_backend_components override.
        """
        pass

    def _get_single_qubit_gate_properties(self, instr_name: Optional[str]) -> dict:
        """Not implemented - gate properties provided by wrapped IQMBackend target.

        This abstract method is required by parent class but not called due to
        _initialize_backend_components override.
        """
        pass

    def _get_multi_qubit_gate_properties(self):
        """Not implemented - gate properties provided by wrapped IQMBackend target.

        This abstract method is required by parent class but not called due to
        _initialize_backend_components override.
        """
        pass

    @property
    def architecture(self):
        return self._iqm_backend.architecture

    @property
    def target_with_resonators(self) -> Target:
        """Return the target with MOVE gates and resonators included.

        Raises:
            ValueError: The backend does not have resonators.

        """
        return self._iqm_backend.target_with_resonators

    @property
    def backend_info(self) -> BackendDto:
        return self._backend_info

    @property
    def backend_provider(self) -> Provider:
        return Provider.IQM

    def configuration(self):
        raise NotImplementedError("Configuration not supported. Use target() method instead.")

    @property
    def coupling_map(self):
        return self._iqm_backend.coupling_map

    @property
    def dt(self):
        return self._iqm_backend.dt

    @property
    def instruction_schedule_map(self):
        raise NotImplementedError("Instruction schedule not supported.")

    @property
    def max_circuits(self):
        return self._iqm_backend.max_circuits

    @property
    def physical_qubits(self):
        return self._iqm_backend.physical_qubits

    def _convert_to_job_input(self, job_input: QuantumCircuit, options: Options = None) -> dict:
        run_request = self._create_run_request(job_input, options)

        return {
            "circuits": run_request["circuits"]
        }


    def _convert_to_job_params(self, job_input: QuantumCircuit = None, options=None) -> dict:
        run_request = self._create_run_request(job_input, options)

        run_request.pop("circuits", None)
        run_request.pop("shots", None)

        return run_request

    def _create_run_request(self, job_input, options) -> dict:
        """Create a run request for IQM backend using the wrapped IQM SDK.

        Args:
            job_input: Quantum circuit to execute
            options: Job execution options including shots and calibration_set_id

        Returns:
            Run request dictionary for IQM execution
        """
        # Get shots with fallback to backend minimum
        shots = options.get("shots")
        if shots is None:
            shots = self.backend_info.configuration.shots_range.min

        run_request = self._iqm_backend.create_run_request(
            run_input=[job_input],
            qubit_mapping=None,
            custom_settings=None,
            calibration_set_id=options.get("calibration_set_id"),
            shots=shots,
            options=options,
        )

        run_request_dict = run_request.model_dump(mode='json')
        return run_request_dict

    def _get_job_input_format(self) -> JobInputFormat:
        return JobInputFormat.IQM_JOB_INPUT_V1

    def has_resonators(self) -> bool:
        """True iff the backend QPU has computational resonators."""
        return self._iqm_backend.has_resonators()

    def get_real_target(self) -> Target:
        """Return the real physical target of the backend without fictional CZ gates."""
        return self._iqm_backend.get_real_target()

    def qubit_name_to_index(self, name: str) -> int:
        """Given an IQM-style qubit name, return the corresponding index in the register.

        Args:
            name: IQM-style qubit name ('QB1', 'QB2', etc.)

        Returns:
            Index of the given qubit in the quantum register.

        Raises:
            ValueError: Qubit name cannot be found on the backend.

        """
        return self._iqm_backend.qubit_name_to_index(name)

    def index_to_qubit_name(self, index: int) -> str:
        """Given a quantum register index, return the corresponding IQM-style qubit name.

        Args:
            index: Qubit index in the quantum register.

        Returns:
            Corresponding IQM-style qubit name ('QB1', 'QB2', etc.).

        Raises:
            ValueError: Qubit index cannot be found on the backend.

        """
        return self._iqm_backend.index_to_qubit_name(index)

    def get_scheduling_stage_plugin(self) -> str:
        """Return the plugin that should be used for scheduling the circuits on this backend."""
        return self._iqm_backend.get_scheduling_stage_plugin()






