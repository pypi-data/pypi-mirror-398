from _typeshed import Incomplete
from bosa_core.authentication.constants import ALREADY_EXISTS_OR_INVALID_DATA as ALREADY_EXISTS_OR_INVALID_DATA, CONSTRAINT_OR_DATA_ERROR as CONSTRAINT_OR_DATA_ERROR, DB_CONNECTION_ERROR_MESSAGE as DB_CONNECTION_ERROR_MESSAGE, ERROR_LOG_MESSAGE as ERROR_LOG_MESSAGE, INVALID_DATA_FORMAT_QUERY as INVALID_DATA_FORMAT_QUERY, INVALID_QUERY_PARAMETERS as INVALID_QUERY_PARAMETERS
from bosa_core.authentication.database import SQLAlchemySQLDataStore as SQLAlchemySQLDataStore
from bosa_core.authentication.user.repository.base_repository import BaseRepository as BaseRepository
from bosa_core.authentication.user.repository.models import UserModel as UserModel
from bosa_core.authentication.user.repository.sqlalchemy.models import DBUser as DBUser
from bosa_core.exception import DatabaseConnectionException as DatabaseConnectionException
from uuid import UUID

class SqlAlchemyUserRepository(BaseRepository):
    """User repository."""
    db: Incomplete
    def __init__(self, data_store: SQLAlchemySQLDataStore) -> None:
        """Initialize the repository.

        Args:
            data_store (SQLAlchemySQLDataStore): Data store.
        """
    def get_user(self, client_id: UUID, user_id: UUID) -> UserModel | None:
        """Retrieves a user.

        Args:
            client_id (UUID): Client ID.
            user_id (UUID): User ID.

        Returns:
            UserModel | None: User object, or None if not found.

        Raises:
            ValueError: If invalid data format provided.
            DatabaseConnectionException: If an error occurs while getting the user.
        """
    def get_user_by_identifier(self, client_id: UUID, identifier: str) -> UserModel | None:
        """Retrieves a user.

        Args:
            client_id (UUID): Client ID.
            identifier (str): User identifier.

        Returns:
            UserModel | None: User object or None if not found.

        Raises:
            ValueError: If invalid data format provided.
            DatabaseConnectionException: If an error occurs while getting the user by identifier.
        """
    def create_user(self, user: UserModel) -> UserModel:
        """Creates a new user.

        Args:
            user (UserModel): User model.

        Returns:
            UserModel: Created user.

        Raises:
            UserAlreadyExistsException: If user already exists or constraint violation.
            DatabaseConnectionException: If an error occurs while creating the user.
        """
