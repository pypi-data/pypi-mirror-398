from _typeshed import Incomplete
from bosa_core.authentication.client.helper.helper import ClientHelper as ClientHelper
from bosa_core.authentication.client.repository.base_repository import BaseRepository as BaseRepository
from bosa_core.authentication.client.repository.models import Client as Client, ClientBasic as ClientBasic

class CreateClientService:
    """Service for creating clients."""
    client_repository: Incomplete
    client_helper: Incomplete
    def __init__(self, client_repository: BaseRepository) -> None:
        """Initialize the service.

        Args:
            client_repository (BaseRepository): The client repository
        """
    def create_client(self, client_name: str, can_get_integrations: bool = False) -> Client:
        """Create client.

        Args:
            client_name (str): The name of the client
            can_get_integrations (bool): Whether the client can get integrations

        Returns:
            Client: The created client
        """
