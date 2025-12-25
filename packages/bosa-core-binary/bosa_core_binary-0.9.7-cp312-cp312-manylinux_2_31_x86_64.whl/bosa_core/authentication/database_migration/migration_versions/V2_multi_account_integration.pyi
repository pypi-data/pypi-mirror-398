import sqlalchemy
from bosa_core.authentication.database_migration.base_migration import DbMigration as DbMigration

class V2multiAccountIntegration(DbMigration):
    """Multi Account Integration database migration class."""
    version: int
    description: str
    def migrate(self, engine: sqlalchemy.Engine):
        """Apply the migration.

        Args:
            engine: The database engine to use for the migration.
        """
