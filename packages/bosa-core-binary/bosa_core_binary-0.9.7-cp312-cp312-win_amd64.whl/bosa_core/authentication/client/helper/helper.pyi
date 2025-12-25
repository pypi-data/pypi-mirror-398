from bosa_core.authentication.client.repository.models import ClientBasic as ClientBasic
from bosa_core.authentication.common.base64_helper import decode_base64 as decode_base64, encode_base64 as encode_base64
from bosa_core.exception import InvalidClientException as InvalidClientException

class ClientHelper:
    """Client helper functions."""
    API_KEY_PREFIX: str
    API_KEY_LENGTH: int
    DELIMITER: str
    def generate_secret(self) -> str:
        """Generate client secret.

        Returns:
            str: The client secret
        """
    def build_api_key(self, client: ClientBasic) -> str:
        """Build API key.

        Args:
            client (ClientBasic): The client to build the API key for

        Returns:
            str: The API key
        """
    def to_client(self, api_key: str) -> ClientBasic:
        """Convert API key to client.

        Args:
            api_key (str): The API key for client authentication

        Returns:
            ClientBasic: The client
        """
