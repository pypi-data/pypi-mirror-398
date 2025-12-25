from bosa_core.authentication.common.base64_helper import decode_base64 as decode_base64, encode_base64 as encode_base64
from bosa_core.authentication.user.repository.models import UserBasic as UserBasic, UserModel as UserModel
from bosa_core.exception import UnauthorizedException as UnauthorizedException

class UserHelper:
    """User helper class."""
    SECRET_PREFIX: str
    SECRET_LENGTH: int
    DELIMITER: str
    def generate_secret(self) -> str:
        """Generate user secret.

        Returns:
            str: The user secret
        """
    def build_api_key(self, user: UserModel) -> str:
        """Build API key.

        Args:
            user (UserModel): The user to build the API key for

        Returns:
            str: The API key
        """
    def to_user(self, secret_key: str) -> UserBasic:
        """Convert secret key to user.

        Args:
            secret_key (str): The secret key

        Returns:
            UserBasic: The user

        Raises:
            UnauthorizedException: If the secret key is invalid
        """
