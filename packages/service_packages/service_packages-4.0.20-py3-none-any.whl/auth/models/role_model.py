from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy.orm import Mapped, mapped_column, relationship


class RoleModel(UUIDAuditBase):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(unique=True)
    users = relationship(
        "UserModel",
        secondary="users_roles",
        back_populates="roles",
        lazy="selectin",
    )
