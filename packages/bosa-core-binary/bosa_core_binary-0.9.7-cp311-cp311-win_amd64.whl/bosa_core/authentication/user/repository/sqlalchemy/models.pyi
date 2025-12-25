from _typeshed import Incomplete
from bosa_core.authentication.database import DatabaseAdapter as DatabaseAdapter
from bosa_core.authentication.token.repository.sqlalchemy.models import DBToken as DBToken

class DBUser(DatabaseAdapter.base):
    """User SQLAlchemy model."""
    __tablename__: str
    id: Incomplete
    identifier: Incomplete
    secret: Incomplete
    secret_preview: Incomplete
    is_active: Incomplete
    client_id: Incomplete
    client: Incomplete
    tokens: Incomplete
