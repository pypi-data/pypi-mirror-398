from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class UserRoleModel(UUIDAuditBase):
    __tablename__ = "users_roles"

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
