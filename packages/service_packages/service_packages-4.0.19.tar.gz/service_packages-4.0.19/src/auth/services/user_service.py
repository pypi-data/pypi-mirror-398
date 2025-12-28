from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import UserModel

__all__ = [
    "UserService",
    "provide_user_service",
]


class UserService(SQLAlchemyAsyncRepositoryService):
    class Repository(SQLAlchemyAsyncRepository[UserModel]):
        model_type = UserModel

    repository_type = Repository


async def provide_user_service(db_session: AsyncSession) -> UserService:
    return UserService(session=db_session)
