from nexo.client.manager import ClientManager
from .config import ClientConfig
from .services.blood_type import BloodTypeClientService
from .services.gender import GenderClientService
from .services.medical_role import MedicalRoleClientService
from .services.medical_service import MedicalServiceClientService
from .services.organization_role import OrganizationRoleClientService
from .services.organization_type import OrganizationTypeClientService
from .services.service import ServiceClientService
from .services.system_role import SystemRoleClientService
from .services.user_type import UserTypeClientService


class MaleoMetadataClientManager(ClientManager[ClientConfig]):
    def initalize_services(self):
        self.blood_type = BloodTypeClientService(
            application_context=self._application_context,
            config=self._config,
            logger=self._logger,
            http_client_manager=self._http_client_manager,
            private_key=self._private_key,
            redis=self._redis,
        )
        self.gender = GenderClientService(
            application_context=self._application_context,
            config=self._config,
            logger=self._logger,
            http_client_manager=self._http_client_manager,
            private_key=self._private_key,
            redis=self._redis,
        )
        self.medical_role = MedicalRoleClientService(
            application_context=self._application_context,
            config=self._config,
            logger=self._logger,
            http_client_manager=self._http_client_manager,
            private_key=self._private_key,
            redis=self._redis,
        )
        self.medical_service = MedicalServiceClientService(
            application_context=self._application_context,
            config=self._config,
            logger=self._logger,
            http_client_manager=self._http_client_manager,
            private_key=self._private_key,
            redis=self._redis,
        )
        self.organization_role = OrganizationRoleClientService(
            application_context=self._application_context,
            config=self._config,
            logger=self._logger,
            http_client_manager=self._http_client_manager,
            private_key=self._private_key,
            redis=self._redis,
        )
        self.organization_type = OrganizationTypeClientService(
            application_context=self._application_context,
            config=self._config,
            logger=self._logger,
            http_client_manager=self._http_client_manager,
            private_key=self._private_key,
            redis=self._redis,
        )
        self.service = ServiceClientService(
            application_context=self._application_context,
            config=self._config,
            logger=self._logger,
            http_client_manager=self._http_client_manager,
            private_key=self._private_key,
            redis=self._redis,
        )
        self.system_role = SystemRoleClientService(
            application_context=self._application_context,
            config=self._config,
            logger=self._logger,
            http_client_manager=self._http_client_manager,
            private_key=self._private_key,
            redis=self._redis,
        )
        self.user_type = UserTypeClientService(
            application_context=self._application_context,
            config=self._config,
            logger=self._logger,
            http_client_manager=self._http_client_manager,
            private_key=self._private_key,
            redis=self._redis,
        )
