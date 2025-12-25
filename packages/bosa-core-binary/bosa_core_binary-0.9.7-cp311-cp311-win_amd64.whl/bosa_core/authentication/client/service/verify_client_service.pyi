from _typeshed import Incomplete
from bosa_core.authentication.client.helper.helper import ClientHelper as ClientHelper
from bosa_core.authentication.client.repository.base_repository import BaseRepository as BaseRepository
from bosa_core.exception import InvalidClientException as InvalidClientException

class VerifyClientService:
    """Service for verifying client API key."""
    client_repository: Incomplete
    client_helper: Incomplete
    def __init__(self, client_repository: BaseRepository) -> None:
        """Initialize the service.

        Args:
            client_repository (BaseRepository): The client repository
        """
    def verify_api_key(self, client_api_key: str) -> None:
        """Verify client API key.

        Args:
            client_api_key (str): The API key for client authentication

        Returns:
            None
        """
    def is_api_key_valid(self, client_api_key: str) -> bool:
        """Check if API key is valid.

        Args:
            client_api_key (str): The API key for client authentication

        Returns:
            bool: True if API key is valid, False otherwise

        Raises:
            InvalidClientException: If the client is not found
        """
