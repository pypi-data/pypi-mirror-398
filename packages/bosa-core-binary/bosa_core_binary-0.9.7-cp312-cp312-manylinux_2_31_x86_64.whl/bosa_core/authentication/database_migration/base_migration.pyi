import abc
from abc import ABC, abstractmethod

class DbMigration(ABC, metaclass=abc.ABCMeta):
    """Base class for database migrations."""
    version: int
    description: str
    @abstractmethod
    def migrate(self, engine):
        """Apply the migration."""
    def record_version(self, engine) -> None:
        """Record the migration version in the database.

        Args:
            engine: The database engine to use for recording the version.
        """
