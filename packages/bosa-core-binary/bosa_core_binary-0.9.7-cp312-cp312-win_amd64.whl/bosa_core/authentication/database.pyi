from _typeshed import Incomplete
from bosa_core.authentication.database_migration.migration import run_migrations as run_migrations
from sqlalchemy.engine import Engine as Engine
from typing import Any

class SQLAlchemySQLDataStore:
    """Data store for interacting with SQLAlchemy.

    This class provides methods to interact with a SQL database using SQLAlchemy.

    Attributes:
        db (Session): The SQLAlchemy session object.
        engine (Engine): The SQLAlchemy engine object.
        logger (Logger): The logger object.
    """
    db: Incomplete
    engine: Incomplete
    def __init__(self, engine_or_url: Engine | str, pool_size: int = 10, max_overflow: int = 10, autoflush: bool = True, **kwargs: Any) -> None:
        """Initialize SQLAlchemySQLDataStore class.

        Args:
            engine_or_url (Engine | str): SQLAlchemy engine object or database URL.
            pool_size (int, optional): The size of the database connections to be maintained. Defaults to 10.
            max_overflow (int, optional): The maximum overflow size of the pool. Defaults to 10.
                This parameter is ignored for SQLite.
            autoflush (bool, optional): If True, all changes to the database are flushed immediately. Defaults to True.
            **kwargs (Any): Additional keyword arguments to support the initialization of the SQLAlchemy adapter.

        Raises:
            ValueError: If the database adapter is not initialized.
        """

class DatabaseAdapter:
    """Initializes a database engine and session using SQLAlchemy.

    Provides a scoped session and a base query property for interacting with the database.
    """
    engine: Incomplete
    db: Incomplete
    base: Incomplete
    @classmethod
    def initialize(cls, engine_or_url: Engine | str, pool_size: int = 10, max_overflow: int = 10, autocommit: bool = False, autoflush: bool = True):
        """Creates a new database engine and session.

        Must provide either an engine or a database URL.

        Args:
            engine_or_url (Engine|str): Sqlalchemy engine object or database URL.
            pool_size (int): The size of the database connections to be maintained. Default is 10.
            max_overflow (int): The maximum overflow size of the pool. Default is 10.
            autocommit (bool): If True, all changes to the database are committed immediately. Default is False.
            autoflush (bool): If True, all changes to the database are flushed immediately. Default is True.
        """
    @classmethod
    def has_table(cls, table_name: str):
        """Check if a table exists in the database.

        Args:
            table_name (str): Table name to check.

        Returns:
            bool: True if table exists in the database.
        """

def initialize_authentication_db(data_store: SQLAlchemySQLDataStore):
    """Initialize the database and do migrations.

    Args:
        data_store (SQLAlchemySQLDataStore): The SQLAlchemy data store.
    """
