from copy import deepcopy
from typing import Tuple, Optional, Any, List

from qiskit.providers import Options
from qiskit.providers.models import QasmBackendConfiguration, BackendProperties
from qiskit.qobj.utils import MeasLevel, MeasReturnType
from qiskit.transpiler import Target
from qiskit_ibm_runtime.ibm_backend import IBMBackend
from qiskit_ibm_runtime.models import BackendStatus
from qiskit_ibm_runtime.utils.backend_converter import convert_to_target
from qiskit_ibm_runtime.utils.backend_decoder import configuration_from_server_data, properties_from_server_data

from planqk.quantum.sdk.client import _PlanqkClient, BackendDto, PlanqkBackendStatus
from planqk.quantum.sdk.client.model_enums import JobInputFormat
from planqk.quantum.sdk.exceptions import PlanqkError
from planqk.quantum.sdk.qiskit import PlanqkQiskitBackend
from planqk.quantum.sdk.qiskit.planqk_qiskit_runtime_service import PlanqkQiskitRuntimeService

"""
PLANQK IBM Backend Implementation

This class is adapted from the IBM Qiskit Runtime's IBMBackend class
(qiskit_ibm_runtime.ibm_backend.IBMBackend) to provide compatibility
with IBM's backend patterns while integrating with the PLANQK SDK.

Original IBM implementation: 
https://github.com/Qiskit/qiskit-ibm-runtime/blob/main/qiskit_ibm_runtime/ibm_backend.py
"""
@PlanqkQiskitRuntimeService.register_backend("ibm.qpu.aachen")
@PlanqkQiskitRuntimeService.register_backend("ibm.qpu.fez")
@PlanqkQiskitRuntimeService.register_backend("ibm.qpu.kingston")
@PlanqkQiskitRuntimeService.register_backend("ibm.qpu.marrakesh")
@PlanqkQiskitRuntimeService.register_backend("ibm.qpu.pittsburgh")
@PlanqkQiskitRuntimeService.register_backend("ibm.qpu.torino")
@PlanqkQiskitRuntimeService.register_backend("ibm.qpu.strasbourg")
@PlanqkQiskitRuntimeService.register_backend("ibm.qpu.brussels")
class PlanqkIbmQiskitBackend(PlanqkQiskitBackend, IBMBackend):
    id_warning_issued = False

    def __init__(self,
                 service: "PlanqkQiskitRuntimeService",
                 planqk_client: _PlanqkClient,
                 backend_info: BackendDto,
                 configuration: Optional[QasmBackendConfiguration] = None,
                 use_fractional_gates: bool = False,
                 **kwargs):
        """Initialize PlanqkIbmQiskitBackend.

        Args:
            service: Instance of QiskitRuntimeService.
            planqk_client: PLANQK client for API communication.
            backend_info: PLANQK backend information.
            configuration: Pre-built backend configuration. If provided, will be used
                         instead of creating from raw backend config.
            use_fractional_gates: Whether to use fractional gates in backend configuration.
            **kwargs: Additional arguments passed to parent constructor.
        """
        self._service = service
        self._properties: Any = None
        self._configuration = configuration
        self._use_fractional_gates = use_fractional_gates

        super().__init__(planqk_client=planqk_client, backend_info=backend_info, **kwargs)

        if hasattr(self, 'options'):
            self.options.use_fractional_gates = use_fractional_gates

    def _initialize_backend_components(self):
        """Override template method for IBM-specific initialization order."""
        self._configuration = self._ibm_backend_config_to_configuration()
        self.properties()
        self._target = self._planqk_backend_to_target()

    def _set_configuration_based_validators(self):
        """Set option validators based on configuration, following IBM's approach."""
        if not hasattr(self, '_configuration') or self._configuration is None:
            return

        if (
                not self._configuration.simulator
                and hasattr(self.options, "noise_model")
                and hasattr(self.options, "seed_simulator")
        ):
            self.options.set_validator("noise_model", type(None))
            self.options.set_validator("seed_simulator", type(None))

        if hasattr(self._configuration, "rep_delay_range"):
            self.options.set_validator(
                "rep_delay",
                (self._configuration.rep_delay_range[0], self._configuration.rep_delay_range[1]),
            )

    @classmethod
    def _default_options(cls) -> Options:
        """Default runtime options."""
        return Options(
            shots=4000,
            memory=False,
            meas_level=MeasLevel.CLASSIFIED,
            meas_return=MeasReturnType.AVERAGE,
            memory_slots=None,
            memory_slot_size=100,
            rep_time=None,
            rep_delay=None,
            init_qubits=True,
            use_measure_esp=None,
            use_fractional_gates=False,
            # Simulator only
            noise_model=None,
            seed_simulator=None,
        )

    def _planqk_backend_to_target(self) -> Target:
        return convert_to_target(
            configuration=self._configuration,
            properties=self._properties,
        )

    def _convert_to_job_input(self, job_input, options=None) -> Tuple[JobInputFormat, dict]:
        # Job create is handled by 'PlanqkQiskitRuntimeService'
        pass

    def _get_job_input_format(self) -> JobInputFormat:
        return JobInputFormat.QISKIT

    def _ibm_backend_config_to_configuration(self) -> QasmBackendConfiguration:
        """Create backend configuration following IBM's approach.
        
        Returns:
            QasmBackendConfiguration: Backend configuration either from provided config
                                     or created from raw backend data.
        """

        # Use provided configuration if available
        if self._configuration is not None:
            self.backend_version = self._configuration.backend_version
            self._set_configuration_based_validators()
            return deepcopy(self._configuration)

        # Otherwise create from raw backend config, for IBM backends the raw config contains the actual backend config and also the properties
        raw_config = self._get_backend_config().get("config", None)
        self.backend_version = raw_config.get("backend_version", None)
        raw_config["backend_name"] = self.name

        return configuration_from_server_data(
            raw_config,
            instance="",
            use_fractional_gates=self._use_fractional_gates,
        )

    @property
    def service(self) -> "qiskit_runtime_service.QiskitRuntimeService":
        """Return the ``service`` object

        Returns:
            service: instance of QiskitRuntimeService
        """
        return self._service

    @property
    def dtm(self) -> float:
        """Return the system time resolution of output signals

        Returns:
            dtm: The output signal timestep in seconds.
        """
        return self._configuration.dtm

    @property
    def meas_map(self) -> List[List[int]]:
        """Return the grouping of measurements which are multiplexed

        This is required to be implemented if the backend supports Pulse
        scheduling.

        Returns:
            meas_map: The grouping of measurements which are multiplexed
        """
        return self._configuration.meas_map

    def properties(
            self, refresh: bool = False
    ) -> Optional[BackendProperties]:
        """Return the backend properties.

        This data describes qubits properties (such as T1 and T2),
        gates properties (such as gate length and error), and other general
        properties of the backend.

        The schema for backend properties can be found in
        `Qiskit/ibm-quantum-schemas/backend_properties
        <https://github.com/Qiskit/ibm-quantum-schemas/blob/main/schemas/backend_properties_schema.json>`_.

        Args:
            refresh: If ``True``, re-query the server for the backend properties.
                Otherwise, return a cached version.

        Returns:
            The backend properties or ``None`` if the backend properties are not
            currently available.

        Raises:
            TypeError: If an input argument is not of the correct type.
        """
        # pylint: disable=arguments-differ
        if self._configuration.simulator:
            # Simulators do not have backend properties.
            return None
        if not isinstance(refresh, bool):
            raise TypeError(
                "The 'refresh' argument needs to be a boolean. "
                "{} is of type {}".format(refresh, type(refresh))
            )
        if refresh or self._properties is None:
            api_properties = self._get_backend_config(refresh).get("properties", None)
            if not api_properties:
                return None
            backend_properties = properties_from_server_data(
                api_properties,
                use_fractional_gates=self.options.use_fractional_gates,
            )
            self._properties = backend_properties
        return self._properties

    def refresh(self):
        """Refresh the backend status and properties.
        
        Raises:
            NotImplementedError: This method is not implemented for PLANQK IBM backends.
        """
        raise NotImplementedError("refresh method not implemented for PLANQK IBM backends.")

    def status(self) -> BackendStatus:
        """Return the backend status.
        
        Returns:
            BackendStatus: The status of the backend.
            
        Raises:
            NotImplementedError: This method is not implemented for PLANQK IBM backends.
        """
        state_info = self._planqk_client.get_backend_state(self.backend_info.id)
        operational = state_info.status == PlanqkBackendStatus.ONLINE
        status_msg = "active" if operational else state_info.status.name.lower()
        pending_jobs = 0

        return BackendStatus.from_dict({'backend_name': self.name,
                                        'backend_version': self.backend_version,
                                        'operational': operational,
                                        'status_msg': status_msg,
                                        'pending_jobs': pending_jobs})

    def target_history(self, datetime=None):
        """Get the target history for this backend.

        Args:
            datetime: Optional datetime to get historical target.

        Returns:
            None - not implemented for PLANQK backends.

        Raises:
            NotImplementedError: This method is not implemented for PLANQK IBM backends.
        """
        raise NotImplementedError("target_history method not implemented for PLANQK IBM backends.")

    def retrieve_job(self, job_id: str):
        """Retrieve a job - not supported for IBM backends.

        Args:
            job_id: Job ID to retrieve.

        Raises:
            PlanqkError: This method is not supported for IBM backends.
        """
        raise PlanqkError(
            "The retrieve_job() method is not supported for IBM backends. "
            "Use the job() method of PlanqkQiskitRuntimeService to retrieve jobs."
        )

    # No need to implement these methods for IBM backends as IBM's backend decoder is used.
    def _to_gate(self, name: str):
        pass

    def _get_single_qubit_gate_properties(self, instr_name: Optional[str]) -> dict:
        # Configuration and properties are handled by IBM's backend decoder.
        pass

    def _get_multi_qubit_gate_properties(self):
        # Configuration and properties are handled by IBM's backend decoder.
        pass


