from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class RolePermissionModel(UUIDAuditBase):
    __tablename__ = "roles_permissions"

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id"), primary_key=True)
