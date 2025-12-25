from _typeshed import Incomplete
from datetime import datetime
from pydantic import BaseModel
from uuid import UUID

class TokenComplete(BaseModel):
    """Token model with complete data."""
    model_config: Incomplete
    id: UUID
    token: str
    token_type: str
    expires_at: datetime
    is_revoked: bool
    user_id: UUID
    client_id: UUID

class Token(BaseModel):
    """Token model."""
    model_config: Incomplete
    id: UUID
    user_id: UUID
    client_id: UUID
    is_revoked: bool
    expires_at: int | None
