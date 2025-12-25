"""
PLANQK Qiskit Runtime Service V2 Implementation

This class is adapted from the IBM Qiskit Runtime's QiskitRuntimeService class
(qiskit_ibm_runtime.qiskit_runtime_service.QiskitRuntimeService) to provide compatibility
with IBM's runtime service patterns while integrating with the PLANQK SDK.

Original IBM implementation: 
https://github.com/Qiskit/qiskit-ibm-runtime/blob/main/qiskit_ibm_runtime/qiskit_runtime_service.py
"""
import json
import warnings
from datetime import datetime
from typing import Dict, Callable, Optional, Union, List, Any, Type, Sequence

from qiskit.providers import QiskitBackendNotFoundError
from qiskit.providers.backend import BackendV2 as Backend
from qiskit_ibm_runtime import ibm_backend, RuntimeOptions, QiskitRuntimeService, RuntimeEncoder
from qiskit_ibm_runtime.accounts import ChannelType
from qiskit_ibm_runtime.runtime_job_v2 import RuntimeJobV2
from qiskit_ibm_runtime.utils.result_decoder import ResultDecoder

from planqk.quantum.sdk.client import Provider, RuntimeJobParamsDto
from planqk.quantum.sdk.client.client import base_url
from planqk.quantum.sdk.client.job_dtos import JobDto
from planqk.quantum.sdk.client.model_enums import JobInputFormat, PlanqkSdkProvider
from planqk.quantum.sdk.qiskit.planqk_qiskit_runtime_job import PlanqkRuntimeJobV2
from planqk.quantum.sdk.qiskit.provider import PlanqkQuantumProvider
from planqk.quantum.sdk.qiskit.providers.ibm.runtime_session_client_adapter import RuntimeSessionClientAdapter


class PlanqkQiskitRuntimeService(PlanqkQuantumProvider, QiskitRuntimeService):
    """PLANQK Runtime Service V2 with full IBM QiskitRuntimeService API compatibility.
    
    This class is adapted from the IBM Qiskit Runtime's QiskitRuntimeService class
    to provide a compatible interface for PLANQK quantum backends while leveraging
    IBM's runtime service patterns. It implements all public methods from the 
    original QiskitRuntimeService for API compatibility.
    
    Note:
        Only the PLANQK channel is supported, as access to IBM backends is handled
        by the PLANQK platform. Users should use the PLANQK CLI for authentication
        and account management (https://docs.platform.planqk.de/cli-reference.html).
    """

    # Channel constant for PLANQK
    _CHANNEL = "PLANQK"

    # Backend mapping for registered IBM backends
    _backend_mapping: Dict[str, Type["PlanqkIbmQiskitBackend"]] = {}

    @classmethod
    def register_backend(cls, backend_id: str):
        """For internal use only. Binds a backend class to a PLANQK IBM backend id.
        
        Args:
            backend_id: PLANQK backend ID for IBM backends (e.g., 'ibm.qpu.aachen').
            
        Returns:
            Decorator function that registers the backend class.
            
        Example:
            @PlanqkQiskitRuntimeServiceV2.register_backend("ibm.qpu.aachen")
            class PlanqkIbmQiskitBackend(PlanqkQiskitBackend):
                pass
        """

        def decorator(backend_cls: Type["PlanqkIbmQiskitBackend"]):
            cls._backend_mapping[backend_id] = backend_cls
            return backend_cls

        return decorator

    def _get_backend_class(self, backend_id: str) -> Type["PlanqkIbmQiskitBackend"]:
        """Get the backend class for a given backend ID.
        
        Args:
            backend_id: PLANQK backend ID for IBM backends.
            
        Returns:
            Backend class if registered, None otherwise.
        """
        return self._backend_mapping.get(backend_id)

    def __init__(
            self, access_token: Optional[str] = None, organization_id: Optional[str] = None, _client=None
    ) -> None:
        """PlanqkQiskitRuntimeServiceV2 constructor.
        
        Args:
            access_token (str): access token used for authentication with PLANQK.
                    If no token is provided, the token is retrieved from the environment variable PLANQK_ACCESS_TOKEN that can be either set
                    manually or by using the PLANQK CLI.
                    Defaults to None.

            organization_id (str, optional): the ID of a PLANQK organization you are member of.
                    Provide this ID if you want to access quantum
                    backends with an organization account and its associated pricing plan.
                    All backend executions (jobs, tasks etc.) you create are visible to the members of the organization.
                    If the ID is omitted, all backend executions are performed under your personal account.
                    Defaults to None.

            _client: (For testing purposes) PLANQK client instance. If not provided,
                    a new client instance will be created.
        """
        # Call parent constructor
        super().__init__(access_token=access_token, organization_id=organization_id, _client=_client)

    def _api_client(self) -> RuntimeSessionClientAdapter:
        """API client for IBM Session compatibility.

        IBM's Session class expects a service._api_client attribute for session operations.
        This property delegates to _get_api_client() for consistency.

        Returns:
            RuntimeSessionClientAdapter: Session runtime client wrapper
        """
        return self._get_api_client()

    def _get_api_client(self, instance: Optional[str] = None) -> RuntimeSessionClientAdapter:
        """Return the API client for session operations.

        This method is called by IBM's Session class to get an API client that handles
        session-related operations. It returns a PlanqkRuntimeSessionClientAdapter that wraps
        the PLANQK client and provides IBM-compatible session management interface.

        Args:
            instance: IBM Cloud instance identifier (ignored - not supported in PLANQK)

        Returns:
            RuntimeSessionClientAdapter: Session runtime client wrapper

        Note:
            The instance parameter is part of the IBM QiskitRuntimeService interface
            and is included for compatibility. It is ignored in the PLANQK integration
            since instance management is handled by the PLANQK platform.
        """
        return RuntimeSessionClientAdapter(self._client)

    def active_account(self) -> Optional[Dict[str, str]]:
        """Return the account currently in use for the session.

        Returns:
            A dictionary with information about the account currently in the session.
        """
        if not self._client:
            return None

        account_info = {
            "channel": self._CHANNEL,
            "url": base_url()
        }

        organization_id = self._client.get_organization_id()
        if organization_id:
            account_info["organization_id"] = organization_id

        return account_info

    def backend(
        self,
        name: str,
        instance: Optional[str] = None,
        use_fractional_gates: Optional[bool] = False,
    ) -> "PlanqkIbmQiskitBackend":
        """Return a single backend matching the PLANQK backend id.

        Note:
            The `instance` parameter is part of the IBM QiskitRuntimeService interface
            and is included here for compatibility. It is ignored in the PLANQK integration
            since instance management is handled by the PLANQK platform.

        This method retrieves a PLANQK backend and validates that it's an IBM backend,
        as Qiskit Runtime only supports IBM quantum backends. Non-IBM backends will
        raise an error.

        Args:
            name: Name of the backend as PLANQK backend id (e.g., 'ibm.qpu.aachen',
                  'ibm.simulator.extended_stabilizer').

            instance: IBM Cloud account CRN - not supported.
            use_fractional_gates: Set True to allow for the backends to include
                fractional gates. Currently this feature cannot be used
                simultaneously with dynamic circuits, PEC, PEA, or gate
                twirling.  When this flag is set, control flow instructions are
                automatically removed from the backend.
                When you use a dynamic circuits feature (e.g. ``if_else``) in your
                algorithm, you must disable this flag to create executable ISA circuits.
                This flag might be modified or removed when our backend
                supports dynamic circuits and fractional gates simultaneously.
                If ``None``, then both fractional gates and control flow operations are
                included in the backends.

        Returns:
            Backend: A PLANQK quantum backend instance for the specified IBM backend.

        Raises:
            QiskitBackendNotFoundError: If the backend is not found or is not an IBM backend.
            
        Example:
            >>> service = PlanqkQiskitRuntimeService()
            >>> backend = service.backend('ibm.qpu.aachen')
            >>> print(backend.name)
            'ibm.qpu.aachen'
        """
        # Get backend info from PLANQK client
        backend_dto = self._client.get_backend(backend_id=name)

        # Validate it's an IBM backend
        if backend_dto.provider != Provider.IBM:
            raise QiskitBackendNotFoundError(
                f"Backend '{name}' is not from IBM. Qiskit Runtime only supports IBM backends.")

        # Get registered backend class
        backend_class = self._get_backend_class(name)
        if backend_class:
            return backend_class(
                service=self,
                planqk_client=self._client,
                backend_info=backend_dto,
                use_fractional_gates=use_fractional_gates
            )
        else:
            raise QiskitBackendNotFoundError(f"IBM backend '{name}' is not registered with PlanqkQiskitRuntimeService.")

    def backends(self, provider: Provider = None) -> List[str]:
        """Return all IBM backends accessible via this service that are registered.

        Returns:
            List[str]: A list of registered IBM backend IDs.
        """
        # Get all IBM backends from parent class
        all_ibm_backend_ids = super().backends(provider=Provider.IBM)

        # Filter to only show registered backends
        registered_backend_ids = [
            backend_id for backend_id in all_ibm_backend_ids
            if backend_id in self._backend_mapping
        ]

        return registered_backend_ids

    def check_pending_jobs(self) -> None:
        """(DEPRECATED) Check the number of pending jobs and wait for the oldest pending job if
        the maximum number of pending jobs has been reached.
        """
        raise NotImplementedError("check_pending_jobs method not yet implemented")

    @staticmethod
    def delete_account(
            filename: Optional[str] = None,
            name: Optional[str] = None,
            channel: Optional[ChannelType] = None,
    ) -> bool:
        """Delete a saved account from disk.

        Note:
            This method is not implemented for PLANQK. Use the PLANQK CLI instead:
            
            To logout: planqk logout

        Returns:
            True if the account was deleted.
        """
        raise NotImplementedError("delete_account method not supported. Use PLANQK CLI: planqk logout")

    def delete_job(self, job_id: str) -> None:
        """(DEPRECATED) Delete a runtime job.

        Note that this operation cannot be reversed.

        Args:
            job_id: Job ID.
        """
        raise NotImplementedError("delete_job method not yet implemented")

    def instances(self) -> List[str]:
        """Return a list that contains a series of dictionaries with the
        following instance identifiers per instance: "crn", "plan", "name".

        Note:
            This method is not implemented for PLANQK. Instance management
            is handled by the PLANQK platform.

        Returns:
            A list with instances available for the active account.
        """
        raise NotImplementedError("instances method not implemented. Instance management is handled by PLANQK platform")

    @classmethod
    def _get_shots(cls, inputs: Dict, backend) -> int:
        """Retrieve shots from inputs with fallback logic.

        Args:
            inputs: Program input parameters
            backend: Backend instance for fallback min_shots

        Returns:
            Number of shots to use
        """
        # Get default shots from backend options, then inputs options, finally backend min_shots
        default_shots = backend.options.get('shots', backend.min_shots) if hasattr(backend, 'options') else backend.min_shots
        options = inputs.get('options', {})
        if 'default_shots' in options:
            default_shots = options['default_shots']

        shots = default_shots  # Default fallback

        # First, try to get shots from first pub
        pubs = inputs.get('pubs', [])
        if pubs and len(pubs) > 0:
            first_pub = pubs[0]
            # Check for shots property in the pub
            if hasattr(first_pub, 'shots') and first_pub.shots is not None:
                shots = first_pub.shots

        # If shots not found in pubs, fall back to run_options (existing logic)
        if shots == default_shots:
            run_options = inputs.get('run_options')
            if run_options is not None:
                shots = run_options.get('shots', default_shots)

        return shots

    def _run(
            self,
            program_id: str,
            inputs: Dict,
            options: Optional[Union[RuntimeOptions, Dict]] = None,
            callback: Optional[Callable] = None,
            result_decoder: Optional[Union[Type[ResultDecoder], Sequence[Type[ResultDecoder]]]] = None,
            session_id: Optional[str] = None,
            start_session: Optional[bool] = False,
            calibration_id: Optional[str] = None,
    ) -> PlanqkRuntimeJobV2:
        """Execute the runtime program.

        Args:
            program_id: Program ID.
            inputs: Program input parameters. These input values are passed
                to the runtime program.
            options: Runtime options that control the execution environment.

            callback: Callback function to be invoked for any interim results and final result.
                The callback function will receive 2 positional parameters:

                    1. Job ID
                    2. Job result.

            result_decoder: A :class:`ResultDecoder` subclass used to decode job results.
                If more than one decoder is specified, the first is used for interim results and
                the second final results. If not specified, a program-specific decoder or the default
                ``ResultDecoder`` is used.
            session_id: Job ID of the first job in a runtime session.
            start_session: Set to True to explicitly start a runtime session. Defaults to False.
            calibration_id: The calibration ID to use for the job execution. Optional parameter
                for specifying custom calibration data.

        Returns:
            A ``RuntimeJobV2`` instance representing the execution.

        Raises:
            IBMInputValueError: If input is invalid.
            RuntimeProgramNotFound: If the program cannot be found.
            IBMRuntimeError: An error occurred running the program.
        """

        if calibration_id is not None:
            warnings.warn(
                "The 'calibration_id' parameter is currently not supported by PLANQK and will be ignored.",
                UserWarning
            )

        qrt_options: RuntimeOptions = options
        if options is None:
            qrt_options = RuntimeOptions()
        elif isinstance(options, Dict):
            qrt_options = RuntimeOptions(**options)

        qrt_options.validate(channel=self.channel)

        backend = qrt_options.backend
        if isinstance(backend, str):
            backend = self.backend(name=qrt_options.get_backend_name())

        status = backend.status()
        if status.operational is True and status.status_msg != "active":
            warnings.warn(
                f"The backend {backend.name} currently has a status of {status.status_msg}."
            )

        version = inputs.get("version", 1) if inputs else 1

        runtime_job_params = RuntimeJobParamsDto(
            program_id=program_id,
            backend_name=qrt_options.get_backend_name(),
            image=qrt_options.image,
            log_level=qrt_options.log_level,
            job_tags=qrt_options.job_tags,
            max_execution_time=qrt_options.max_execution_time,
            start_session=start_session,
            session_time=qrt_options.session_time,
            version=version,
            private=qrt_options.private,
        )

        backend_id = backend.name
        shots = self._get_shots(inputs, backend)

        input_params = runtime_job_params.model_dump()

        # Encode inputs with RuntimeEncoder for Qiskit serialization, then parse back to dict
        # This ensures proper Qiskit object serialization while providing a dict structure
        encoded_input_json = json.dumps(inputs, cls=RuntimeEncoder)
        parsed_inputs = json.loads(encoded_input_json)

        job_request = JobDto(backend_id=backend_id,
                             provider=Provider.IBM,
                             input_format=JobInputFormat.QISKIT_QPY,
                             input=parsed_inputs,
                             shots=shots,
                             session_id=session_id,
                             input_params=input_params,
                             sdk_provider=PlanqkSdkProvider.QISKIT)

        return PlanqkRuntimeJobV2(backend=backend, job_details=job_request, result_decoder=result_decoder, planqk_client=self._client, provider=self)

    def job(self, job_id: str) -> RuntimeJobV2:
        """Retrieve a runtime job.

        Args:
            job_id: Job ID.

        Returns:
            Runtime job retrieved from the service.
        """
        return self.retrieve_job(job_id)

    def jobs(
            self,
            limit: Optional[int] = 10,
            skip: int = 0,
            backend_name: Optional[str] = None,
            pending: bool = None,
            program_id: str = None,
            instance: Optional[str] = None,
            job_tags: Optional[List[str]] = None,
            session_id: Optional[str] = None,
            created_after: Optional[datetime] = None,
            created_before: Optional[datetime] = None,
            descending: bool = True,
    ) -> List[RuntimeJobV2]:
        """Retrieve all runtime jobs, subject to optional filtering.

        Args:
            limit: Number of jobs to retrieve.
            skip: Starting index for the job retrieval.
            backend_name: Name of the backend to retrieve jobs from.
            pending: Filter by job pending state.
            program_id: Filter by program ID.
            instance: This is only supported on IBM cloud channel.
            job_tags: Filter by job tags.
            session_id: Job's session ID.
            created_after: Filter by created date after this date.
            created_before: Filter by created date before this date.
            descending: If ``True``, return the jobs in descending order of the job
                creation date.

        Returns:
            A list of runtime jobs.
        """
        raise NotImplementedError("jobs method not yet implemented")

    def least_busy(
            self,
            min_num_qubits: Optional[int] = None,
            instance: Optional[str] = None,
            filters: Optional[Callable[["ibm_backend.IBMBackend"], bool]] = None,
            **kwargs: Any,
    ) -> "ibm_backend.IBMBackend":
        """Return the least busy available backend.

        Args:
            min_num_qubits: Minimum number of qubits the backend has to have.
            instance: This is only supported on IBM cloud channel.
            filters: Filtering conditions as a callable.
            **kwargs: Simple filters that specify a ``True``/``False`` criteria.

        Returns:
            The backend with the fewest number of pending jobs.
        """
        raise NotImplementedError("least_busy method not yet implemented")

    @staticmethod
    def save_account(
            token: Optional[str] = None,
            url: Optional[str] = None,
            instance: Optional[str] = None,
            channel: Optional[ChannelType] = None,
            filename: Optional[str] = None,
            name: Optional[str] = None,
            proxies: Optional[dict] = None,
            verify: Optional[bool] = None,
            overwrite: Optional[bool] = False,
            set_as_default: Optional[bool] = None,
            private_endpoint: Optional[bool] = False,
            region: Optional[str] = None,
            plans_preference: Optional[str] = None,
            tags: Optional[List[str]] = None,
    ) -> None:
        """Save the account to disk for future use.

        Note:
            This method is not implemented for PLANQK. Use the PLANQK CLI instead.
            
            To login as user: planqk login
            To login with organization: planqk set-context <org-id>
        """
        raise NotImplementedError("save_account method not supported. Use PLANQK CLI: planqk login")

    @staticmethod
    def saved_accounts(
            default: Optional[bool] = None,
            channel: Optional[ChannelType] = None,
            filename: Optional[str] = None,
            name: Optional[str] = None,
    ) -> dict:
        """List the accounts saved on disk.

        Note:
            This method is not implemented for PLANQK. Use the PLANQK CLI instead.

            To get current context: planqk get-context
            To list all available contexts: planqk list-contexts

        Returns:
            A dictionary with information about the accounts saved on disk.
        """
        raise NotImplementedError("saved_accounts method not supported. Use PLANQK CLI: planqk get-context")

    def usage(self) -> Dict[str, Any]:
        """Return usage information for the current active instance.

        Returns:
            Dict with usage details.
        """
        raise NotImplementedError("usage method not yet implemented")

    @property
    def channel(self) -> str:
        """Return the channel type used.

        Returns:
            The channel type used.
        """
        return self._CHANNEL

    def active_instance(self) -> str:
        """Return the crn of the current active instance.
        
        Note:
            This method is not implemented for PLANQK. Instance management
            is handled by the PLANQK platform.
        
        Returns:
            The active instance identifier.
            
        Raises:
            NotImplementedError: Instance management is handled by PLANQK platform.
        """
        raise NotImplementedError("active_instance method not supported. Instance management is handled by PLANQK platform.")
