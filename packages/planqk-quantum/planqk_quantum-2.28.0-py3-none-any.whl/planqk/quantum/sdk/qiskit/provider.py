import json
from abc import ABC
from typing import List, Dict, Type, Optional, Union

from planqk.quantum.sdk.client.backend_dtos import BackendDto, BackendInfo
from planqk.quantum.sdk.client.backend_factory import BackendInfoFactory
from planqk.quantum.sdk.client.client import _PlanqkClient
from planqk.quantum.sdk.client.job_dtos import JobSummary
from planqk.quantum.sdk.client.model_enums import Provider
from planqk.quantum.sdk.exceptions import PlanqkClientError, BackendNotFoundError, PlanqkError
from planqk.quantum.sdk.qiskit.backend import PlanqkQiskitBackend
from planqk.quantum.sdk.qiskit.job_factory import PlanqkQiskitJobFactory


class _PlanqkProvider(ABC):
    def __init__(self, access_token: str = None, organization_id: str = None, _client=None):
        """Initialize the PLANQK provider.
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

                    _client (_PlanqkClient, optional): Client instance used for making requests to the PLANQK API.
                        This parameter is mainly intended for testing purposes.
                        Defaults to None.
        """
        self._client = _client or _PlanqkClient(access_token=access_token, organization_id=organization_id)


class PlanqkQuantumProvider(_PlanqkProvider):
    _backend_mapping: Dict[str, Type[PlanqkQiskitBackend]] = {}

    @classmethod
    def register_backend(cls, backend_id: str):
        """For internal use only. Binds a backend class to a PLANQK backend id."""

        def decorator(backend_cls: Type[PlanqkQiskitBackend]):
            cls._backend_mapping[backend_id] = backend_cls
            return backend_cls

        return decorator

    def backends(self, provider: Provider = None, detailed: bool = False) -> Union[List[str], List[BackendInfo]]:
        """Return the list of backends supported by PLANQK.

        Args:
            provider: Filter by cloud provider (e.g., Provider.AWS). Defaults to None (all providers).
            detailed: If True, returns BackendInfo objects with SDK support information.
                     If False (default), returns only backend IDs as strings.

        Returns:
            List[str]: Backend IDs when detailed=False.
            List[BackendInfo]: Detailed backend information when detailed=True

        Example:
            >>> provider = PlanqkQuantumProvider()
            >>> # Get just backend IDs (default)
            >>> backend_ids = provider.backends()
            >>> print(backend_ids)
            ['azure.ionq.simulator', 'aws.ionq.aria', ...]

            >>> # Get detailed information including SDK support
            >>> backend_infos = provider.backends(detailed=True)
            >>> for info in backend_infos:
            ...     print(f"{info.id}: {info.supported_sdks}")
            azure.ionq.simulator: {'PlanqkQuantumProvider'}
            aws.ionq.aria: {'PlanqkQuantumProvider', 'PlanqkBraketProvider'}
        """
        backend_dtos = self._client.get_backends()

        # Filter backends (exclude DWAVE, apply provider filter)
        filtered_backends = [
            backend_info for backend_info in backend_dtos
            if (provider is None or backend_info.provider == provider) and backend_info.provider != Provider.DWAVE
        ]

        if not detailed:
            return [backend_info.id for backend_info in filtered_backends]

        # Return detailed BackendInfo objects using the factory
        return [BackendInfoFactory.from_backend_dto(backend_dto) for backend_dto in filtered_backends]

    def get_backend(self, backend_id: str) -> PlanqkQiskitBackend:
        """Return a single backend matching the specified filtering.

        Args:
            backend_id: name of the backend.
            sdk: the SDK to use. Note, that backends must be supported by the SDK.
            **kwargs: dict used for filtering.

        Returns:
            Backend: a backend matching the filtering criteria.

        Raises:
            BackendNotFoundError: if no backend could be found or more than one backend matches the filtering criteria.
        """
        try:
            backend_dto = self._client.get_backend(backend_id=backend_id)
        except PlanqkClientError as e:
            if e.response.status_code == 404:
                text = e.response.text
                if text:
                    error_detail = json.loads(e.response.text)
                    raise BackendNotFoundError("No backend matches the criteria. Reason: " + error_detail['error'])
                else:
                    raise BackendNotFoundError("No backend matches the criteria.")
            raise e

        backend_state_dto = self._client.get_backend_state(backend_id=backend_id)
        if backend_state_dto:
            backend_dto.status = backend_state_dto.status

        return self._get_backend_object(backend_dto)

    def _get_backend_object(self, backend_info: BackendDto) -> PlanqkQiskitBackend:
        backend_class = self._get_backend_class(backend_info.id)

        if backend_class:
            return backend_class(planqk_client=self._client, backend_info=backend_info)
        else:
            # Provide helpful error message for IBM backends
            if backend_info.provider == Provider.IBM:
                raise BackendNotFoundError(
                    f"IBM backend '{backend_info.id}' cannot be accessed through PlanqkQuantumProvider. "
                    f"IBM Quantum backends require using PlanqkQiskitRuntimeService instead.\n\n"
                    f"Migration guide:\n"
                    f"  Replace: provider = PlanqkQuantumProvider()\n"
                    f"           backend = provider.get_backend('{backend_info.id}')\n\n"
                    f"  With:    service = PlanqkQiskitRuntimeService()\n"
                    f"           backend = service.backend('{backend_info.id}')\n\n"
                    f"Note: PlanqkQiskitRuntimeService provides full compatibility with IBM's Qiskit Runtime API, "
                    f"including Session and Batch execution modes."
                )
            else:
                raise BackendNotFoundError(f"Qiskit backend '{backend_info.id}' is not supported.")

    def _get_backend_class(self, backend_id: str) -> Type[PlanqkQiskitBackend]:
        return self._backend_mapping.get(backend_id)

    @classmethod
    def create_registered_backend(cls, backend_id: str, planqk_client: "_PlanqkClient") -> Optional[PlanqkQiskitBackend]:
        """Create a backend instance from registered backends.
        
        This static method allows other components to create backend instances
        without directly importing provider-specific implementations.
        
        Args:
            backend_id: PLANQK backend ID.
            planqk_client: PLANQK client instance.
            
        Returns:
            Backend instance if registered, None otherwise.
        """
        backend_class = cls._backend_mapping.get(backend_id)
        if backend_class is None:
            return None
            
        try:
            # Get backend info from client
            backend_dto = planqk_client.get_backend(backend_id=backend_id)
            return backend_class(planqk_client=planqk_client, backend_info=backend_dto)
        except Exception:
            # Return None if backend creation fails
            return None

    def retrieve_job(self, job_id: str) -> 'PlanqkQiskitJob':
        """
        Retrieve a job.

        Args:
            job_id (str): the job id.

        Returns:
            Job: the job from the backend with the given id.
        """
        job_details = self._client.get_job(job_id=job_id)

        backend_id = job_details.backend_id
        backend_class = self._get_backend_class(backend_id)
        if backend_class is None:
            raise PlanqkError(f"Job '{job_id}' was created on backend '{backend_id}'. This backend is not supported by Qiskit.")

        return PlanqkQiskitJobFactory.create_job(backend=None, job_id=job_id, job_details=job_details, planqk_client=self._client, provider=self)

    def jobs(self) -> List[JobSummary]:
        """
        Returns an overview on all jobs of the user or an organization.

        For each job the following attributes are returned:
            - job_id (str): The unique identifier of the job.
            - provider_name (Provider): The job provider.
            - backend_id (str): The identifier of the backend used.
            - created_at (datetime): The timestamp when the job was created.

        Returns:
            List[JobSummary]: A list of basic job information.
        """
        print("Getting your jobs from PLANQK, this may take a few seconds...")
        job_dtos = self._client.get_jobs()
        return [
            JobSummary(
                id=job_dto.id,
                provider=job_dto.provider,
                backend_id=job_dto.backend_id,
                created_at=job_dto.created_at
            )
            for job_dto in job_dtos
        ]
