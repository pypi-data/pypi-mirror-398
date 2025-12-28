from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy.orm import Mapped, mapped_column


class PermissionModel(UUIDAuditBase):
    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(unique=True)
