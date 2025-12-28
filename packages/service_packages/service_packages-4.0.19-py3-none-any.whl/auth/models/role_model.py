from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy.orm import Mapped, mapped_column


class RoleModel(UUIDAuditBase):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(unique=True)
