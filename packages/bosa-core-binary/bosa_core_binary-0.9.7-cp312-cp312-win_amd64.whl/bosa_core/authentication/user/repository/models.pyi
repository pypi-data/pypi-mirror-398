from _typeshed import Incomplete
from bosa_core.authentication.plugin.repository.models import ThirdPartyIntegrationAuthBasic as ThirdPartyIntegrationAuthBasic
from pydantic import BaseModel
from uuid import UUID

class UserBasic(BaseModel):
    """Basic User Information for further processing."""
    id: UUID
    identifier: str
    secret: str

class User(BaseModel):
    """User model for public use."""
    model_config: Incomplete
    id: UUID | None
    identifier: str
    secret_preview: str
    is_active: bool
    client_id: UUID

class UserModel(User):
    """User model for internal use."""
    secret: str

class UserComplete(User):
    """User model with integration list."""
    integrations: list[ThirdPartyIntegrationAuthBasic]
