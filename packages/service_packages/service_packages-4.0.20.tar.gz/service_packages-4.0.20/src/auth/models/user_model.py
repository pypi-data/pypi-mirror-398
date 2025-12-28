from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy.orm import Mapped, mapped_column, relationship


class UserModel(UUIDAuditBase):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    is_email_verified: Mapped[bool]
    is_enabled: Mapped[bool]

    roles = relationship(
        "RoleModel",
        secondary="users_roles",
        back_populates="users",
        lazy="selectin",
    )
