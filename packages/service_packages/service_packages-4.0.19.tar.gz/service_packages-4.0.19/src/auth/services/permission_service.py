from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import PermissionModel

__all__ = ["PermissionService", "provide_permission_service"]


class PermissionService(SQLAlchemyAsyncRepositoryService):
    class Repository(SQLAlchemyAsyncRepository[PermissionModel]):
        model_type = PermissionModel

    repository_type = Repository


async def provide_permission_service(db_session: AsyncSession) -> PermissionService:
    return PermissionService(session=db_session)
