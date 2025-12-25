from _typeshed import Incomplete
from datetime import datetime
from pydantic import BaseModel
from uuid import UUID

class Client(BaseModel):
    """Client model for public use."""
    id: UUID
    name: str
    api_key: str
    is_active: bool
    created_at: datetime | None
    can_get_integrations: bool

class ClientBasic(BaseModel):
    """Client model with only the basic values for validation."""
    model_config: Incomplete
    id: UUID
    name: str
    secret: str
    can_get_integrations: bool

class ClientModel(ClientBasic):
    """Client model for internal purposes."""
    is_active: bool
    created_at: datetime | None
