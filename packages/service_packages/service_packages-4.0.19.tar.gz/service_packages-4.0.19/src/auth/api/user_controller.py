from typing import Annotated

from advanced_alchemy.extensions.litestar.dto import SQLAlchemyDTO, SQLAlchemyDTOConfig
from advanced_alchemy.extensions.litestar.providers import create_service_dependencies
from advanced_alchemy.filters import FilterTypes
from advanced_alchemy.service import OffsetPagination
from litestar import delete, get, post
from litestar.controller import Controller
from litestar.params import Dependency
import msgspec

from ..models import UserModel
from ..services import UserService


class UserCreateRequest(msgspec.Struct):
    email: str
    password: str
    is_email_verified: bool
    is_enabled: bool


class UserDTO(SQLAlchemyDTO[UserModel]):
    config = SQLAlchemyDTOConfig(exclude={"password"})


class UserController(Controller):
    dependencies = create_service_dependencies(
        UserService,
        key="service",
        filters={
            "created_at": True,
            "updated_at": True,
            "sort_field": "email",
            "search": "email",
        },
    )
    return_dto = UserDTO

    @get(operation_id="ListUsers", path="/users")
    async def list_users(
        self,
        service: UserService,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[UserModel]:
        results, total = await service.list_and_count(*filters)
        return service.to_schema(data=results, total=total, filters=filters)

    @post(operation_id="CreateUser", path="/users")
    async def create_user(self, service: UserService, data: UserCreateRequest) -> UserModel:
        return await service.create(UserModel(**msgspec.to_builtins(data)), auto_commit=True)

    @delete(operation_id="DeleteUser", path="/users/{item_id:str}")
    async def delete_user(self, service: UserService, item_id: str) -> None:
        await service.delete(item_id, auto_commit=True)
