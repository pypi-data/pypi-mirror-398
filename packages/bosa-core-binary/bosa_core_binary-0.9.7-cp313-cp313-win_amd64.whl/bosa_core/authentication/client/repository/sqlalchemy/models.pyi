from _typeshed import Incomplete
from bosa_core.authentication.database import DatabaseAdapter as DatabaseAdapter
from bosa_core.authentication.plugin.repository.sqlalchemy.models import DBThirdPartyIntegrationAuth as DBThirdPartyIntegrationAuth
from bosa_core.authentication.user.repository.sqlalchemy.models import DBUser as DBUser

class DBClient(DatabaseAdapter.base):
    """Client SQLAlchemy model."""
    __tablename__: str
    id: Incomplete
    name: Incomplete
    secret: Incomplete
    is_active: Incomplete
    created_at: Incomplete
    can_get_integrations: Incomplete
    users: Incomplete
    integrations: Incomplete
