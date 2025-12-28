from typing import Any

from auth.models import UserModel
from auth.services import AuthService, PermissionService, RoleService, UserService


class AuthLoader:
    def __init__(
        self,
        user_service: UserService,
        role_service: RoleService,
        permission_service: PermissionService,
    ):
        self.user_service = user_service
        self.role_service = role_service
        self.permission_service = permission_service

    async def load(self, data: dict[str, Any]):
        await self.user_service.create_many(
            [
                UserModel(
                    email=user["email"],
                    password=AuthService.hash_password(user["password"]),
                    is_enabled=True,
                    is_email_verified=True,
                )
                for user in data.get("users", [])
            ],
            auto_commit=True,
        )
