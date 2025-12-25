from _typeshed import Incomplete
from bosa_core.authentication.client.service.client_aware_service import ClientAwareService as ClientAwareService
from bosa_core.authentication.plugin.repository.models import ThirdPartyIntegrationAuthBasic as ThirdPartyIntegrationAuthBasic
from bosa_core.authentication.plugin.service.third_party_integration_service import ThirdPartyIntegrationService as ThirdPartyIntegrationService
from bosa_core.authentication.user.repository.base_repository import BaseRepository as BaseRepository
from bosa_core.authentication.user.repository.models import UserComplete as UserComplete, UserModel as UserModel
from uuid import UUID

class GetUserService:
    """Get user service."""
    client_aware_service: Incomplete
    user_repository: Incomplete
    third_party_integration_service: Incomplete
    def __init__(self, user_repository: BaseRepository, client_aware_service: ClientAwareService, third_party_integration_service: ThirdPartyIntegrationService) -> None:
        """Initialize the service.

        Args:
            user_repository (BaseRepository): The user repository
            client_aware_service (IClientAwareService): The client aware service
            third_party_integration_service (IThirdPartyIntegrationService): The third-party integration service
        """
    def get_user(self, api_key: str, user_id: UUID) -> UserModel:
        """Get user.

        Args:
            api_key (str): The API key for client authentication
            user_id (UUID): The user ID

        Returns:
            UserModel: The user model

        Raises:
            InvalidClientException: If the client is not found
            UnauthorizedException: If the user is not found
        """
    def get_user_by_client_id(self, client_id: UUID, user_id: UUID) -> UserModel:
        """Get user by client ID.

        Args:
            client_id (UUID): The client ID
            user_id (UUID): The user ID

        Returns:
            UserModel: The user model

        Raises:
            UnauthorizedException: If the user is not found
        """
    def get_user_by_identifier(self, api_key: str, identifier: str) -> UserModel:
        """Get user by identifier.

        Args:
            api_key (str): The API key for client authentication
            identifier (str): The user identifier

        Returns:
            UserModel: The user model

        Raises:
            InvalidClientException: If the client is not found
            UnauthorizedException: If the user is not found
        """
    def get_user_complete(self, api_key: str, user_id: UUID) -> UserComplete:
        """Get user complete.

        Args:
            api_key (str): The API key for client authentication
            user_id (UUID): The user ID

        Returns:
            UserComplete: The user complete

        Raises:
            InvalidClientException: If the client is not found
            UnauthorizedException: If the user is not found
        """
