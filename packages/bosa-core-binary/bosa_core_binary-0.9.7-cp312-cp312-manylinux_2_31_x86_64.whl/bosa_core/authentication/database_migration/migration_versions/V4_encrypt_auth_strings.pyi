import sqlalchemy
from _typeshed import Incomplete
from bosa_core.authentication.database_migration.base_migration import DbMigration as DbMigration
from bosa_core.authentication.security.encryption_manager import EncryptionManager as EncryptionManager

logger: Incomplete

class V4EncryptAuthStrings(DbMigration):
    """Migration to encrypt existing plaintext auth_strings."""
    version: int
    description: str
    def migrate(self, engine: sqlalchemy.Engine):
        """Encrypt all plaintext auth_strings in the database.

        Args:
            engine: The database engine to use for the migration.
        """
