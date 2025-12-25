import sqlalchemy
from bosa_core.authentication.database_migration.base_migration import DbMigration as DbMigration

class V3AddIntegrationIndexes(DbMigration):
    """Add essential indexes for authentication tables."""
    version: int
    description: str
    def migrate(self, engine: sqlalchemy.Engine):
        """Apply the migration.

        Args:
            engine: The database engine to use for the migration.
        """
