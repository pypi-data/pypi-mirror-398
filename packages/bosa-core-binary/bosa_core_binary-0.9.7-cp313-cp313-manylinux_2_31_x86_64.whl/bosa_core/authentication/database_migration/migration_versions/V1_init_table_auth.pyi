from bosa_core.authentication.database_migration.base_migration import DbMigration as DbMigration

class V1initTableAuth(DbMigration):
    """Init auth database v1."""
    version: int
    description: str
    def migrate(self, engine) -> None:
        """Apply the migration.

        Args:
            engine: The database engine to use for the migration.
        """
