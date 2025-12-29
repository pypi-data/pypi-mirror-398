from nexo.client.manager import ClientManager
from .config import ClientConfig
from .services.organization_registration_code import (
    OrganizationRegistrationCodeClientService,
)
from .services.organization_relation import OrganizationRelationClientService
from .services.organization import OrganizationClientService
from .services.patient import PatientClientService
from .services.user_medical_role import UserMedicalRoleClientService
from .services.user_organization_role import UserOrganizationRoleClientService
from .services.user_organization import UserOrganizationClientService
from .services.user_profile import UserProfileClientService
from .services.user_system_role import UserSystemRoleClientService
from .services.user import UserClientService


class MaleoIdentityClientManager(ClientManager[ClientConfig]):
    def initalize_services(self):
        self.organization_registration_code = OrganizationRegistrationCodeClientService(
            application_context=self._application_context,
            config=self._config,
            logger=self._logger,
            http_client_manager=self._http_client_manager,
            private_key=self._private_key,
            redis=self._redis,
        )
        self.organization_relation = OrganizationRelationClientService(
            application_context=self._application_context,
            config=self._config,
            logger=self._logger,
            http_client_manager=self._http_client_manager,
            private_key=self._private_key,
            redis=self._redis,
        )
        self.organization = OrganizationClientService(
            application_context=self._application_context,
            config=self._config,
            logger=self._logger,
            http_client_manager=self._http_client_manager,
            private_key=self._private_key,
            redis=self._redis,
        )
        self.patient = PatientClientService(
            application_context=self._application_context,
            config=self._config,
            logger=self._logger,
            http_client_manager=self._http_client_manager,
            private_key=self._private_key,
            redis=self._redis,
        )
        self.user_medical_role = UserMedicalRoleClientService(
            application_context=self._application_context,
            config=self._config,
            logger=self._logger,
            http_client_manager=self._http_client_manager,
            private_key=self._private_key,
            redis=self._redis,
        )
        self.user_organization_role = UserOrganizationRoleClientService(
            application_context=self._application_context,
            config=self._config,
            logger=self._logger,
            http_client_manager=self._http_client_manager,
            private_key=self._private_key,
            redis=self._redis,
        )
        self.user_organization = UserOrganizationClientService(
            application_context=self._application_context,
            config=self._config,
            logger=self._logger,
            http_client_manager=self._http_client_manager,
            private_key=self._private_key,
            redis=self._redis,
        )
        self.user_profile = UserProfileClientService(
            application_context=self._application_context,
            config=self._config,
            logger=self._logger,
            http_client_manager=self._http_client_manager,
            private_key=self._private_key,
            redis=self._redis,
        )
        self.user_system_role = UserSystemRoleClientService(
            application_context=self._application_context,
            config=self._config,
            logger=self._logger,
            http_client_manager=self._http_client_manager,
            private_key=self._private_key,
            redis=self._redis,
        )
        self.user = UserClientService(
            application_context=self._application_context,
            config=self._config,
            logger=self._logger,
            http_client_manager=self._http_client_manager,
            private_key=self._private_key,
            redis=self._redis,
        )
