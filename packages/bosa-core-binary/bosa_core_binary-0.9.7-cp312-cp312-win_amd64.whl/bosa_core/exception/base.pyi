from _typeshed import Incomplete

class BosaException(Exception):
    """Base exception."""
    status_code: Incomplete
    extra_info: Incomplete
    def __init__(self, message: str, *, status_code: int, extra_info: dict = None) -> None:
        """Initialize the exception.

        Args:
            message (str): The message of the exception.
            status_code (int): The status code of the exception.
            extra_info (dict, optional): Additional information about the exception. Default is None.
        """

class UninitializedException(BosaException):
    """Exception raised when database adapter is not initialized."""
    def __init__(self, message: str = 'Database adapter is not initialized.') -> None:
        '''Initialize the exception.

        Args:
            message (str): The message of the exception. Default is "Database adapter is not initialized.".
        '''

class DatabaseConnectionException(BosaException):
    """Exception raised when database connection fails."""
    def __init__(self, message: str | None = 'Database connection failed') -> None:
        '''Initialize the exception.

        Args:
            message (str): The message of the exception. Default is "Database connection failed".
        '''

class UnauthorizedException(BosaException):
    """Exception raised when user is unauthorized."""
    def __init__(self, message: str | None = 'Unauthorized') -> None:
        '''Initialize the exception.

        Args:
            message (str): The message of the exception. Default is "Unauthorized".
        '''

class InvalidClientException(BosaException):
    """Exception raised when client is invalid."""
    def __init__(self, message: str | None = 'Client not found') -> None:
        '''Initialize the exception.

        Args:
            message (str): The message of the exception. Default is "Client not found".
        '''

class UserAlreadyExistsException(BosaException):
    """Exception raised when user already exists."""
    def __init__(self, message: str | None = 'User already exists') -> None:
        '''Initialize the exception.

        Args:
            message (str): The message of the exception. Default is "User already exists".
        '''

class NotFoundException(BosaException):
    """Exception raised when a resource is not found."""
    def __init__(self, message: str | None = 'Not found') -> None:
        '''Initialize the exception.

        Args:
            message (str): The message of the exception. Default is "Not found".
        '''
