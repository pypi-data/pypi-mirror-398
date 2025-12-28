from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from litestar.middleware import (
    AbstractAuthenticationMiddleware,
    AuthenticationResult,
)

from core.storage import Storage

from .services import provide_auth_service, provide_user_service
from .services.auth_service import TOKEN_PREFIX, AuthService


class JWTAuthMiddleware(AbstractAuthenticationMiddleware):
    async def authenticate_request(self, connection: ASGIConnection) -> AuthenticationResult:
        auth_header = connection.headers.get("Authorization")
        if not auth_header:
            raise NotAuthorizedException()

        token = auth_header.replace(f"{TOKEN_PREFIX} ", "")
        auth_service: AuthService = await self._get_auth_service(connection)

        return AuthenticationResult(
            user=await auth_service.check_token(token, connection.headers.get("User-Agent")),
            auth=token,
        )

    @staticmethod
    async def _get_auth_service(connection: ASGIConnection) -> AuthService:
        storage: Storage = await connection.app.dependencies.get("storage")()
        db_session = await connection.app.dependencies.get("db_session")(
            state=connection.app.state,
            scope=connection.scope,
        )
        mail_client = await connection.app.dependencies.get("mail_client")()
        user_service = await provide_user_service(db_session=db_session)
        async for auth_service in provide_auth_service(
            db_session=db_session,
            mail_client=mail_client,
            storage=storage,
            user_service=user_service,
        ):
            return auth_service
