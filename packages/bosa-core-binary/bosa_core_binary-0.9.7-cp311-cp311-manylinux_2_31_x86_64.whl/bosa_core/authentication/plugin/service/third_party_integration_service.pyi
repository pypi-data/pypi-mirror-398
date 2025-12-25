from _typeshed import Incomplete
from bosa_core.authentication.plugin.repository.base_repository import BaseRepository as BaseRepository
from bosa_core.authentication.plugin.repository.models import ThirdPartyIntegrationAuth as ThirdPartyIntegrationAuth
from bosa_core.authentication.security.encryption_manager import EncryptionManager as EncryptionManager
from bosa_core.exception.base import NotFoundException as NotFoundException, UserAlreadyExistsException as UserAlreadyExistsException
from uuid import UUID

class ThirdPartyIntegrationService:
    """Third-party integration service."""
    DEFAULT_INTEGRATION_NOT_FOUND_MESSAGE: str
    third_party_integration_repository: Incomplete
    encryption_manager: Incomplete
    def __init__(self, third_party_integration_repository: BaseRepository) -> None:
        """Initialize the service.

        Args:
            third_party_integration_repository (BaseRepository): The third-party integration repository
        """
    def has_integration(self, client_id: UUID, user_id: UUID, connector: str) -> bool:
        """Returns whether the user has at least one third-party integration for the specified connector.

        Args:
            client_id (UUID): Client ID.
            user_id (UUID): User ID.
            connector (str): Connector name.

        Returns:
            bool: True if the user has at least one third-party integration for the specified connector,
                False otherwise.
        """
    def get_integration(self, client_id: UUID, user_id: UUID, connector: str, user_identifier: str) -> ThirdPartyIntegrationAuth | None:
        """Returns the third-party integration for the specified connector and user identifier.

        Args:
            client_id (UUID): Client ID.
            user_id (UUID): User ID.
            connector (str): Connector name.
            user_identifier (str): User identifier.

        Returns:
            ThirdPartyIntegrationAuth | None: Third-party integration, or None if not found.
        """
    def get_specific_or_default_integration(self, client_id: UUID, user_id: UUID, connector: str, user_identifier: str | None = None) -> ThirdPartyIntegrationAuth | None:
        """Returns the third-party integration for the specified connector.

        If user_identifier is not provided, returns the selected (default) third-party integration.

        Args:
            client_id (UUID): Client ID.
            user_id (UUID): User ID.
            connector (str): Connector name.
            user_identifier (str | None): User identifier.

        Returns:
            ThirdPartyIntegrationAuth | None: Third-party integration, or None if not found.
        """
    def get_integrations(self, client_id: UUID, user_id: UUID, connector: str | None = None) -> list[ThirdPartyIntegrationAuth]:
        """Returns all third-party integrations for the specified client and user, across all connectors.

        If connector is provided, returns all third-party integrations for the specified connector.

        Args:
            client_id (UUID): Client ID.
            user_id (UUID): User ID.
            connector (Optional[str]): Connector name.

        Returns:
            list[ThirdPartyIntegrationAuth]: List of all third-party integrations for the user.
        """
    def create_integration(self, integration: ThirdPartyIntegrationAuth) -> ThirdPartyIntegrationAuth:
        """Creates a third-party integration.

        Args:
            integration (ThirdPartyIntegrationAuth): Third-party integration.

        Returns:
            ThirdPartyIntegrationAuth: Created third-party integration.

        Raises:
            UserAlreadyExistsException: If the user already has an integration for the specified connector.
        """
    def update_integration_auth(self, integration: ThirdPartyIntegrationAuth, auth_string: str, auth_scopes: list[str]) -> ThirdPartyIntegrationAuth:
        """Updates a third-party integration auth string and scopes.

        Args:
            integration (ThirdPartyIntegrationAuth): Third-party integration.
            auth_string (str): New authentication string.
            auth_scopes (list[str]): New authentication scopes.

        Returns:
            ThirdPartyIntegrationAuth: Updated third-party integration.

        Raises:
            NotFoundException: If the integration is not found.
        """
    def delete_integration(self, client_id: UUID, user_id: UUID, connector: str, user_identifier: str) -> None:
        """Deletes a third-party integration by user identifier for the specified connector.

        Args:
            client_id (UUID): Client ID.
            user_id (UUID): User ID.
            connector (str): Connector name.
            user_identifier (str): User identifier.

        Raises:
            NotFoundException: If the integration is not found.
        """
    def set_selected_integration(self, client_id: UUID, user_id: UUID, connector: str, user_identifier: str) -> None:
        """Sets the selected third-party integration for the specified connector.

        Only one integration per connector can be selected at a time.

        Args:
            client_id (UUID): Client ID.
            user_id (UUID): User ID.
            connector (str): Connector name.
            user_identifier (str): User identifier.

        Raises:
            NotFoundException: If the integration is not found.
        """
    def get_integrations_by_connector(self, connector: str) -> list[ThirdPartyIntegrationAuth]:
        """Returns all third-party integrations for a specific connector.

        Args:
            connector (str): Connector name.

        Returns:
            list[ThirdPartyIntegrationAuth]: List of third-party integrations for the specified connector.
        """
    def delete_integrations(self, integration_ids: list[UUID]) -> None:
        """Deletes multiple third-party integrations.

        Args:
            integration_ids (list[UUID]): List of third-party integration IDs.
        """
