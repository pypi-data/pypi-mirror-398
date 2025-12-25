import sqlalchemy
from _typeshed import Incomplete
from bosa_core.authentication.database_migration.base_migration import DbMigration as DbMigration

logger: Incomplete

class V6AddFieldTokenExpire(DbMigration):
    """Base class for database migrations."""
    version: int
    description: str
    def migrate(self, engine: sqlalchemy.Engine):
        """Apply the migration.

        Args:
            engine: The database engine to use for the migration.
        """
