from _typeshed import Incomplete
from bosa_core.authentication.client.service.client_aware_service import ClientAwareService as ClientAwareService
from bosa_core.authentication.config import AuthenticationDbSettings as AuthenticationDbSettings
from bosa_core.authentication.user.helper.helper import UserHelper as UserHelper
from bosa_core.authentication.user.repository.base_repository import BaseRepository as BaseRepository
from bosa_core.authentication.user.repository.models import UserModel as UserModel
from bosa_core.exception.base import UserAlreadyExistsException as UserAlreadyExistsException

class CreateUserService:
    """Create user service."""
    USER_SECRET_PREVIEW_LENGTH: int
    client_aware_service: Incomplete
    user_repository: Incomplete
    user_helper: Incomplete
    hash_service: Incomplete
    def __init__(self, user_repository: BaseRepository, client_aware_service: ClientAwareService) -> None:
        """Initialize the service.

        Args:
            user_repository (BaseRepository): The user repository
            client_aware_service (IClientAwareService): The client aware service
        """
    def create_user(self, api_key: str, identifier: str) -> UserModel:
        """Create user.

        Args:
            api_key (str): The API key for client authentication
            identifier (str): The user identifier

        Returns:
            UserModel: The user model
        """
