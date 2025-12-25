import abc
from abc import ABC, abstractmethod
from bosa_core.authentication.token.repository.models import Token as Token
from uuid import UUID

class BaseRepository(ABC, metaclass=abc.ABCMeta):
    """Base repository interface."""
    @abstractmethod
    def get_token(self, client_id: UUID, user_id: UUID, token_id: UUID) -> Token | None:
        """Get token.

        Args:
            client_id (UUID): The client ID
            user_id (UUID): The user ID
            token_id (UUID): The token ID (jti)

        Returns:
            Token | None: The token

        Raises:
            ValueError: If invalid data format provided.
            DatabaseConnectionException: If an error occurs while getting the token.
        """
    @abstractmethod
    def create_token(self, token: Token) -> None:
        """Create token.

        Args:
            token (Token): The token

        Raises:
            ValueError: If token already exists or constraint violation.
            DatabaseConnectionException: If an error occurs while creating the token.
        """
    @abstractmethod
    def revoke_token(self, client_id: UUID, user_id: UUID, token_id: UUID) -> bool:
        """Revoke a token.

        Args:
            client_id (UUID): The client ID
            user_id (UUID): The user ID
            token_id (UUID): The token ID (jti)

        Returns:
            bool: True if token was found and revoked, False otherwise

        Raises:
            ValueError: If invalid data format provided.
            DatabaseConnectionException: If an error occurs while revoking the token.
        """
    @abstractmethod
    def update_token(self, token: Token) -> bool:
        """Update token's data in the database.

        Args:
            token (Token): Token model containing identifiers and new values.

        Returns:
            bool: True if token was updated, False otherwise.

        Raises:
            ValueError: If constraint violation or invalid data.
            DatabaseConnectionException: If an error occurs while updating the token.
        """
