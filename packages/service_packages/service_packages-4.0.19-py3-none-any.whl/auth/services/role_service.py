from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import RoleModel

__all__ = [
    "RoleService",
    "provide_role_service",
]


class RoleService(SQLAlchemyAsyncRepositoryService):
    class Repository(SQLAlchemyAsyncRepository[RoleModel]):
        model_type = RoleModel

    repository_type = Repository


async def provide_role_service(db_session: AsyncSession) -> RoleService:
    return RoleService(session=db_session)
