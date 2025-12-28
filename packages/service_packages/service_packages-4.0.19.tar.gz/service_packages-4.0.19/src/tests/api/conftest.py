from typing import AsyncIterator

from litestar import Litestar
from litestar.testing import AsyncTestClient
import pytest

from auth.factories import UserFactory
from auth.services import AuthService, LoginRequestDTO, SignUpRequestDTO


@pytest.fixture(scope="session")
async def http_api_client(application) -> AsyncIterator[AsyncTestClient[Litestar]]:
    async with AsyncTestClient(app=application) as client:
        yield client


@pytest.fixture(scope="function")
async def admin_api_client(
    http_api_client: AsyncTestClient, auth_service: AuthService
) -> AsyncIterator[AsyncTestClient[Litestar]]:
    user = UserFactory.build()
    auth_code = await auth_service.signup(SignUpRequestDTO(email=user.email, password=user.password))
    await auth_service.activate_user(auth_code.code, "testclient")
    login_data = await auth_service.login(
        LoginRequestDTO(email=user.email, password=user.password, device="testclient")
    )
    http_api_client.headers["Authorization"] = f"Bearer {login_data.token}"
    yield http_api_client
