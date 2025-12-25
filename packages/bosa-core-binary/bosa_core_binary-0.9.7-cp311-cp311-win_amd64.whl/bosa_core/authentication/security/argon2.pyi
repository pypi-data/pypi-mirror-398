from bosa_core.authentication.security.hash import PasswordHashService as PasswordHashService

class Argon2PasswordHashService(PasswordHashService):
    """Argon2 Password Hash Service."""
    def hash(self, password: str) -> str:
        """Hashes a password.

        Args:
            password: The password to hash.

        Returns:
            The hashed password.
        """
    def verify(self, password: str, hashed_password: str) -> bool:
        """Verifies a password against a hashed password.

        Args:
            password: The password to verify.
            hashed_password: The hashed password.

        Returns:
            True if the password is correct, False otherwise.
        """
