from _typeshed import Incomplete
from bosa_core.authentication.client.helper.helper import ClientHelper as ClientHelper
from bosa_core.authentication.client.repository.base_repository import BaseRepository as BaseRepository
from bosa_core.authentication.client.repository.models import Client as Client, ClientModel as ClientModel
from bosa_core.authentication.client.service.verify_client_service import VerifyClientService as VerifyClientService
from bosa_core.exception import InvalidClientException as InvalidClientException
from uuid import UUID

class ClientAwareService:
    """Services marked by this abstract class are client-aware.

    These services will have access to the client information via the api_key or client_id method.
    """
    ERROR_CLIENT_NOT_FOUND: str
    client_repository: Incomplete
    verify_client_service: Incomplete
    client_helper: Incomplete
    def __init__(self, client_repository: BaseRepository) -> None:
        """Initialize the service.

        Args:
            client_repository (BaseRepository): The client repository
        """
    def get_client_by_api_key(self, api_key: str) -> ClientModel:
        """Get client by API key.

        Args:
            api_key (str): The API key for client authentication

        Returns:
            ClientModel: The client

        Raises:
            InvalidClientException: If the client is not found
        """
    def get_client_id_by_api_key(self, api_key: str) -> UUID:
        """Get client ID by API key.

        Args:
            api_key (str): The API key for client authentication

        Returns:
            UUID: The client ID

        Raises:
            InvalidClientException: If the client is not found
        """
    def get_client_by_id(self, client_id: UUID) -> ClientModel:
        """Get a client by their unique ID.

        Args:
            client_id: The UUID of the client to retrieve

        Returns:
            The ClientModel instance if found

        Raises:
            InvalidClientException: If no client with the given ID exists
        """
    def get_client_list(self) -> list[Client]:
        """Get a list of all clients.

        Returns:
            list[Client]: A list of all clients.
        """
    def update_client(self, x_api_key: str, name: str | None, can_get_integrations: bool | None) -> Client:
        """Update a client.

        Args:
            x_api_key (str): The API key of the client.
            name (str): The name of the client.
            can_get_integrations (bool): Whether the client can get integrations.

        Returns:
            Client: The updated client.
        """
