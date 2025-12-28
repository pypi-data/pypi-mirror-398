from typing import Any
from uuid import UUID

from litestar import Controller, Request, get, post
from litestar.datastructures import State
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_400_BAD_REQUEST
import msgspec

from auth.services import (
    AuthService,
    AccountDTO,
    LoginRequestDTO,
    LogoutRequestDTO,
    SignUpRequestDTO,
    UserNotEnabledError,
    provide_auth_service,
    provide_user_service,
    InvalidEmailError,
    InvalidPasswordError,
)
from auth.services.auth_service import AccountUserDTO


class SignUpRequestScheme(msgspec.Struct):
    email: str
    password: str


class SignUpResponseScheme(msgspec.Struct):
    message: str


class LoginResponseScheme(AccountDTO): ...


class ActivateAccountResponseScheme(AccountDTO): ...


class LoginRequestScheme(msgspec.Struct):
    email: str
    password: str


class ActivateAccountRequestScheme(msgspec.Struct):
    code: str


class AccountController(Controller):
    path = "/account"

    dependencies = {
        "user_service": Provide(provide_user_service),
        "auth_service": Provide(provide_auth_service),
    }

    @get("/me")
    async def account(self, request: Request[AccountDTO, Any, State]) -> AccountDTO:
        return request.user

    @post("/login", exclude_from_auth=True)
    async def login(self, request: Request, data: LoginRequestScheme, auth_service: AuthService) -> LoginResponseScheme:
        device = request.headers.get("User-Agent")

        try:
            login_user = await auth_service.login(
                LoginRequestDTO(
                    email=data.email,
                    password=data.password,
                    device=device,
                )
            )
        except UserNotEnabledError:
            raise HTTPException(f"User {data.email} is not enabled", status_code=HTTP_400_BAD_REQUEST)
        except InvalidEmailError:
            raise HTTPException(f"User with email {data.email} not found", status_code=HTTP_400_BAD_REQUEST)
        except InvalidPasswordError:
            raise HTTPException("Invalid password", status_code=HTTP_400_BAD_REQUEST)

        return LoginResponseScheme(
            token=login_user.token,
            session_id=login_user.session_id,
            user=login_user.user,
        )

    @post("/signup", exclude_from_auth=True)
    async def sign_up(self, data: SignUpRequestScheme, auth_service: AuthService) -> SignUpResponseScheme:
        await auth_service.signup(SignUpRequestDTO(email=data.email, password=data.password))
        return SignUpResponseScheme(message="success")

    @post("/logout")
    async def logout(self, auth_service: AuthService, request: Request[AccountDTO, Any, State]) -> None:
        await auth_service.logout(
            LogoutRequestDTO(
                user_id=request.user.user.id,
                session_id=request.user.session_id,
                device=request.headers.get("User-Agent"),
            )
        )

    @post("/activate", exclude_from_auth=True)
    async def activate(
        self,
        data: ActivateAccountRequestScheme,
        auth_service: AuthService,
        request: Request,
    ) -> ActivateAccountResponseScheme:
        device = request.headers.get("User-Agent")
        activated_account = await auth_service.activate_user(data.code, device)

        return ActivateAccountResponseScheme(
            token=activated_account.token,
            session_id=activated_account.session_id,
            user=activated_account.user,
        )
