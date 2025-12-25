from typing import TypeVar

U = TypeVar('U')

class ConfigService:
    """Service for accessing environment variables with type conversion."""
    @staticmethod
    def get_string(key: str, default: str | None = None) -> str | None:
        """Get environment variable as string."""
    @staticmethod
    def get_int(key: str, default: int | None = None) -> int | None:
        """Get environment variable as integer."""
    @staticmethod
    def get_float(key: str, default: float | None = None) -> float | None:
        """Get environment variable as float."""
    @staticmethod
    def get_bool(key: str, default: bool | None = None) -> bool | None:
        """Get environment variable as boolean.

        'true', 'yes', '1', 'on' are considered True
        'false', 'no', '0', 'off' are considered False
        """
    @staticmethod
    def get_list(key: str, separator: str = ',', default: list[str] | None = None) -> list[str] | None:
        """Get environment variable as list of strings."""
    @staticmethod
    def require(key: str) -> str:
        """Get required environment variable.

        Raises:
            ValueError: If environment variable is not set
        """
    @staticmethod
    def require_as(key: str, type_: type[U]) -> U:
        """Get required environment variable with type conversion.

        Args:
            key: Environment variable key
            type_: Type to convert to (int, float, bool)

        Raises:
            ValueError: If environment variable is not set or cannot be converted
        """
