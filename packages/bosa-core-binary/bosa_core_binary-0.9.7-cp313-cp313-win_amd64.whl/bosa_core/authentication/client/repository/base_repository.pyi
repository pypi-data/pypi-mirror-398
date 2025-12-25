import abc
from abc import ABC, abstractmethod
from bosa_core.authentication.client.repository.models import ClientBasic as ClientBasic, ClientModel as ClientModel
from uuid import UUID

class BaseRepository(ABC, metaclass=abc.ABCMeta):
    """Base repository interface."""
    @abstractmethod
    def create_client(self, client: ClientBasic) -> ClientModel:
        """Create client.

        Args:
            client (ClientBasic): The client to create.

        Returns:
            ClientModel: The created client.

        Raises:
            ValueError: If client already exists or constraint violation.
            DatabaseConnectionException: If an error occurs while creating the client.
        """
    @abstractmethod
    def get_client_by_id(self, client_id: UUID) -> ClientModel | None:
        """Get client by id.

        Args:
            client_id (UUID): The client ID.

        Returns:
            ClientModel | None: The client, or None if not found.

        Raises:
            ValueError: If invalid data format provided.
            DatabaseConnectionException: If an error occurs while getting the client.
        """
    @abstractmethod
    def get_client_list(self) -> list[ClientModel]:
        """Get list of clients.

        Returns:
            list[ClientModel]: A list of all clients.

        Raises:
            DatabaseConnectionException: If an error occurs while getting the client list.
        """
    @abstractmethod
    def update_client(self, client: ClientModel) -> ClientModel | None:
        """Update client.

        Args:
            client (ClientModel): The client to update.

        Returns:
            ClientModel | None: The updated client.

        Raises:
            ValueError: If the client is not found or constraint violation.
            DatabaseConnectionException: If an error occurs while updating the client.
        """
