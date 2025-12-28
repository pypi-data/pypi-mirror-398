from typing import AsyncGenerator
from uuid import UUID
from litestar.exceptions import NotAuthorizedException

import msgspec
import pytest

from auth.factories import UserFactory
from auth.services import (
    AuthService,
    InvalidEmailError,
    InvalidPasswordError,
    LoginRequestDTO,
    LogoutRequestDTO,
    SignUpRequestDTO,
    UserNotEnabledError,
    UserService,
    WrongAuthCodeError,
    AccountDTO,
)
from tests.integrations import TestMailClient


class AuthInfoFixture(msgspec.Struct):
    user_id: UUID
    email: str
    code: str
    password: str


@pytest.fixture
async def auth_info(auth_service: AuthService) -> AsyncGenerator[AuthInfoFixture]:
    user = UserFactory.build()
    auth_code = await auth_service.signup(SignUpRequestDTO(email=user.email, password=user.password))
    yield AuthInfoFixture(
        user_id=auth_code.user_id,
        email=user.email,
        password=user.password,
        code=auth_code.code,
    )
    await auth_service.user_service.delete(auth_code.user_id)


async def test_auth_signup(auth_service: AuthService, mail_client: TestMailClient, user_service: UserService):
    user = UserFactory.build()
    auth_code = await auth_service.signup(SignUpRequestDTO(email=user.email, password=user.password))
    assert mail_client.messages == [([user.email], "Sign up", auth_code.code)]

    created_user = await user_service.get(auth_code.user_id)
    assert created_user.email == user.email

    # teardown
    await auth_service.user_service.delete(auth_code.user_id)


async def test_auth_login_success(auth_service: AuthService, auth_info: AuthInfoFixture):
    activated_user = await auth_service.activate_user(auth_info.code, "testclient")
    account_session = await auth_service.login(
        LoginRequestDTO(
            email=auth_info.email,
            password=auth_info.password,
            device="testclient",
        )
    )
    assert account_session.user.id == activated_user.user.id


async def test_auth_login_wrong_auth_code(auth_info: AuthInfoFixture, auth_service: AuthService):
    with pytest.raises(WrongAuthCodeError):
        await auth_service.activate_user("12345678", "testclient")


async def test_auth_login_user_not_enabled(auth_info: AuthInfoFixture, auth_service: AuthService):
    with pytest.raises(UserNotEnabledError):
        await auth_service.login(
            LoginRequestDTO(email=auth_info.email, password=auth_info.password, device="testclient")
        )


async def test_auth_login_wrong_email(auth_service: AuthService, auth_info: AuthInfoFixture):
    await auth_service.activate_user(auth_info.code, "testclient")

    with pytest.raises(InvalidEmailError):
        await auth_service.login(
            LoginRequestDTO(email="wrong@mail.com", password=auth_info.password, device="testclient")
        )


async def test_auth_login_wrong_password(auth_service: AuthService, auth_info: AuthInfoFixture):
    await auth_service.activate_user(auth_info.code, "testclient")

    with pytest.raises(InvalidPasswordError):
        await auth_service.login(LoginRequestDTO(email=auth_info.email, password="wrong_password", device="testclient"))


async def test_auth_get_account(auth_service: AuthService, auth_info: AuthInfoFixture):
    activated_user = await auth_service.activate_user(auth_info.code, "testclient")
    account_session = await auth_service.login(
        LoginRequestDTO(
            email=auth_info.email,
            password=auth_info.password,
            device="testclient",
        )
    )
    assert account_session.user.id == activated_user.user.id
    account = await auth_service.get_account(account_session.token)
    assert account.user.id == activated_user.user.id


async def test_auth_logout_success(auth_service: AuthService, auth_info: AuthInfoFixture):
    activated_user = await auth_service.activate_user(auth_info.code, "testclient")
    account_session = await auth_service.login(
        LoginRequestDTO(
            email=auth_info.email,
            password=auth_info.password,
            device="testclient",
        )
    )
    account = await auth_service.get_account(account_session.token)

    await auth_service.logout(
        LogoutRequestDTO(
            user_id=activated_user.user.id,
            device="testclient",
            session_id=account_session.session_id,
        )
    )

    with pytest.raises(NotAuthorizedException):
        await auth_service.check_session(
            account,
            "testclient",
        )
