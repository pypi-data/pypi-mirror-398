from _typeshed import Incomplete
from typing import Any

logger: Incomplete

class EncryptionManager:
    """Manages encryption and decryption of sensitive authentication information.

    Using AES-256-GCM authenticated encryption.
    """
    MINIMUM_KEY_LENGTH: int
    MINIMUM_ITERATIONS: int
    def __new__(cls) -> EncryptionManager:
        """Create or return the singleton instance.

        Returns:
            EncryptionManager: The singleton instance
        """
    def __init__(self) -> None:
        """Initialize the encryption manager (only runs once).

        Args:
            encryption_key (Optional[str]): Optional encryption key. If not provided, uses environment variable.
        """
    def encrypt(self, data: str | dict[str, Any]) -> str:
        """Encrypt authentication data (OAuth tokens, API keys, etc.).

        Args:
            data(Union[str, Dict[str, Any]]): String or dictionary containing authentication data
        Returns:
            str: Base64 encoded encrypted string (nonce + ciphertext)
        """
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt an encrypted authentication string back to original format.

        Args:
            encrypted_data(str): Base64 encoded encrypted string (nonce + ciphertext)

        Returns:
            str: Decrypted authentication data as string
        """
