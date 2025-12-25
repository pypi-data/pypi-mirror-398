from _typeshed import Incomplete
from bosa_core.authentication.config import AuthenticationDbSettings as AuthenticationDbSettings
from bosa_core.authentication.token.repository.base_repository import BaseRepository as BaseRepository
from bosa_core.authentication.token.repository.models import Token as Token, TokenComplete as TokenComplete
from bosa_core.authentication.user.repository.models import User as User
from bosa_core.cache.interface import CacheService as CacheService
from datetime import datetime

class CreateTokenService:
    """Create Token Service."""
    cache_service: Incomplete
    token_repository: Incomplete
    def __init__(self, cache_service: CacheService, token_repository: BaseRepository) -> None:
        """Initialize the service.

        Args:
            cache_service (CacheService): The cache service
            token_repository (BaseRepository): The token repository
        """
    def create_token(self, user: User) -> TokenComplete:
        """Create token.

        Args:
            user: The user

        Returns:
            TokenComplete: The token complete
        """
    def get_token_expiration(self) -> tuple[datetime, int]:
        """Get token expiration time and TTL from current date and settings.

        This is a helper function that calculates the expiration datetime and TTL in seconds
        based on the current time and the configured token expiration duration from settings.
        This ensures consistent token expiration across creation and extension operations.

        Returns:
            tuple[datetime, int]: A tuple containing (expiration_datetime, ttl_in_seconds)
        """
