from _typeshed import Incomplete
from bosa_core.authentication.database import DatabaseAdapter as DatabaseAdapter

class DBToken(DatabaseAdapter.base):
    """Token SQLAlchemy model."""
    __tablename__: str
    id: Incomplete
    user_id: Incomplete
    client_id: Incomplete
    is_revoked: Incomplete
    expires_at: Incomplete
    user: Incomplete
