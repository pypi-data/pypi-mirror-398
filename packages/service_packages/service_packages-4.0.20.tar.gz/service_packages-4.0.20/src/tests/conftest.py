from typing import AsyncGenerator

import pytest

from auth.factories import PermissionFactory, RoleFactory, UserFactory
from auth.services import (
    AuthService,
    PermissionService,
    provide_auth_service,
    provide_permission_service,
    provide_role_service,
    provide_user_service,
)
from core.storage import Storage
from tests.integrations import TestMailClient


@pytest.fixture
async def user_service(db_session):
    return await provide_user_service(db_session)


@pytest.fixture
async def role_service(db_session):
    return await provide_role_service(db_session)


@pytest.fixture
async def auth_service(
    db_session,
    mail_client: TestMailClient,
    user_service,
    application,
    storage: Storage,
) -> AsyncGenerator[AuthService, None]:
    async for auth_service in provide_auth_service(
        db_session=db_session,
        mail_client=mail_client,
        storage=storage,
        user_service=user_service,
    ):
        yield auth_service
    mail_client.reset()
    await storage.disconnect()


@pytest.fixture
async def permission_service(db_session) -> PermissionService:
    return await provide_permission_service(db_session)


@pytest.fixture
async def users_fixture(user_service):
    users = await user_service.create_many([UserFactory.build() for _ in range(10)], auto_commit=True)

    yield users
    await user_service.delete_many([user.id for user in users])


@pytest.fixture
async def roles_fixture(role_service):
    roles = await role_service.create_many(
        [RoleFactory.build() for _ in range(10)],
        auto_commit=True,
    )
    yield roles
    await role_service.delete_many([role.id for role in roles])


@pytest.fixture
async def permissions_fixture(permission_service):
    permissions = await permission_service.create_many([PermissionFactory.build() for _ in range(10)], auto_commit=True)
    yield permissions
    await permission_service.delete_many([permission.id for permission in permissions])
