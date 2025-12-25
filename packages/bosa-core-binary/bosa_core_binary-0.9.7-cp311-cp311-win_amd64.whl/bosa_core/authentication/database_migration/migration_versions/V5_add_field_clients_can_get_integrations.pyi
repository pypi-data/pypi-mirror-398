from _typeshed import Incomplete
from bosa_core.authentication.database_migration.base_migration import DbMigration as DbMigration

logger: Incomplete

class V5AddFieldClientsCanGetIntegrations(DbMigration):
    """Base class for database migrations."""
    version: int
    description: str
    def migrate(self, engine) -> None:
        """Apply the migration.

        Args:
            engine: The database engine to use for the migration.
        """
