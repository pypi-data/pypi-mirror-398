import abc
from abc import ABC, abstractmethod

class PasswordHashService(ABC, metaclass=abc.ABCMeta):
    """Base class for password hashing services."""
    @abstractmethod
    def hash(self, password: str) -> str:
        """Hashes a password.

        Args:
            password: The password to hash.

        Returns:
            The hashed password.
        """
    @abstractmethod
    def verify(self, password: str, hashed_password: str) -> bool:
        """Verifies a password against a hashed password.

        Args:
            password: The password to verify.
            hashed_password: The hashed password.

        Returns:
            True if the password is correct, False otherwise.
        """
