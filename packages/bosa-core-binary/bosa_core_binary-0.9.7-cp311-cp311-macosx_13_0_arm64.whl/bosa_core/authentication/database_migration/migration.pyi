from bosa_core.authentication.database_migration.migration_versions.V1_init_table_auth import V1initTableAuth as V1initTableAuth
from bosa_core.authentication.database_migration.migration_versions.V2_multi_account_integration import V2multiAccountIntegration as V2multiAccountIntegration
from bosa_core.authentication.database_migration.migration_versions.V3_add_integration_indexes import V3AddIntegrationIndexes as V3AddIntegrationIndexes
from bosa_core.authentication.database_migration.migration_versions.V4_encrypt_auth_strings import V4EncryptAuthStrings as V4EncryptAuthStrings
from bosa_core.authentication.database_migration.migration_versions.V5_add_field_clients_can_get_integrations import V5AddFieldClientsCanGetIntegrations as V5AddFieldClientsCanGetIntegrations
from bosa_core.authentication.database_migration.migration_versions.V6_add_field_token_expire import V6AddFieldTokenExpire as V6AddFieldTokenExpire

def run_migrations(engine, current_version: int = 0):
    """Run database migrations to update the schema to the latest version.

    This function scans the migration_versions directory for migration files,
    sorts them by version number, and applies each migration in order if its
    version is greater than the current version.

    Args:
        engine: The database engine to use for running migrations.
        current_version (int): The current version of the database schema. Defaults to 0.
    """
