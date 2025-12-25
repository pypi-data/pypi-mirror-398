from bosa_core.authentication.security.argon2 import Argon2PasswordHashService as Argon2PasswordHashService
from bosa_core.authentication.security.hash import PasswordHashService as PasswordHashService

class AuthenticationDbSettings:
    """Authentication Database Connection Settings."""
    database_authentication_url: str
    auth_secret_key: str
    auth_algorithm: str
    auth_access_token_expire_minutes: int
    password_hash_service: PasswordHashService
    def __new__(cls, **kwargs):
        """Singleton pattern implementation."""
    def __init__(self, *, database_authentication_url: str | None = None, auth_secret_key: str | None = None, auth_algorithm: str | None = None, auth_access_token_expire_minutes: int | None = None) -> None:
        '''Initialize the settings.

        Args:
            database_authentication_url (str, optional): The database authentication URL. Defaults to None.
            auth_secret_key (str, optional): The authentication secret key. Defaults to None.
            auth_algorithm (str, optional): The authentication algorithm. Defaults to "HS256".
            auth_access_token_expire_minutes (int, optional): The access token expire minutes. Defaults to 43200.
        '''
