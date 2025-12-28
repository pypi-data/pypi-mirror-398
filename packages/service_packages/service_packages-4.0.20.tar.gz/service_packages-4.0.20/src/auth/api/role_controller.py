from typing import Annotated

from advanced_alchemy.extensions.litestar.dto import SQLAlchemyDTO, SQLAlchemyDTOConfig
from advanced_alchemy.extensions.litestar.providers import create_service_dependencies
from advanced_alchemy.filters import FilterTypes
from advanced_alchemy.service import OffsetPagination
from litestar import delete, get, post
from litestar.controller import Controller
from litestar.params import Dependency
import msgspec

from ..models import RoleModel
from ..services import RoleService


class RoleCreateRequest(msgspec.Struct):
    name: str


class RoleDTO(SQLAlchemyDTO[RoleModel]):
    config = SQLAlchemyDTOConfig()


class RoleController(Controller):
    dependencies = create_service_dependencies(
        RoleService,
        key="service",
        filters={
            "created_at": True,
            "updated_at": True,
        },
    )
    return_dto = RoleDTO

    @get(operation_id="ListRoles", path="/roles")
    async def list_roles(
        self,
        service: RoleService,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[RoleModel]:
        results, total = await service.list_and_count(*filters)
        return service.to_schema(data=results, total=total, filters=filters)

    @post(operation_id="CreateRole", path="/roles")
    async def create_role(self, service: RoleService, data: RoleCreateRequest) -> RoleModel:
        return await service.create(RoleModel(**msgspec.to_builtins(data)), auto_commit=True)

    @delete(operation_id="DeleteRole", path="/roles/{item_id:str}")
    async def delete_role(self, service: RoleService, item_id: str) -> None:
        await service.delete(item_id, auto_commit=True)
