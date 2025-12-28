from typing import Annotated

from advanced_alchemy.extensions.litestar.dto import SQLAlchemyDTO, SQLAlchemyDTOConfig
from advanced_alchemy.extensions.litestar.providers import create_service_dependencies
from advanced_alchemy.filters import FilterTypes
from advanced_alchemy.service import OffsetPagination
from litestar import delete, get, post
from litestar.controller import Controller
from litestar.params import Dependency
import msgspec

from ..models import PermissionModel
from ..services import PermissionService


class PermissionCreateRequest(msgspec.Struct):
    name: str


class PermissionDTO(SQLAlchemyDTO[PermissionModel]):
    config = SQLAlchemyDTOConfig()


class PermissionController(Controller):
    dependencies = create_service_dependencies(
        PermissionService,
        key="service",
        filters={
            "created_at": True,
            "updated_at": True,
        },
    )
    return_dto = PermissionDTO

    @get(operation_id="ListPermissions", path="/permissions")
    async def list_permissions(
        self,
        service: PermissionService,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[PermissionModel]:
        results, total = await service.list_and_count(*filters)
        return service.to_schema(data=results, total=total, filters=filters)

    @post(operation_id="CreatePermission", path="/permissions")
    async def create_permission(self, service: PermissionService, data: PermissionCreateRequest) -> PermissionModel:
        return await service.create(PermissionModel(**msgspec.to_builtins(data)), auto_commit=True)

    @delete(operation_id="DeletePermission", path="/permissions/{item_id:str}")
    async def delete_permission(self, service: PermissionService, item_id: str) -> None:
        await service.delete(item_id, auto_commit=True)
