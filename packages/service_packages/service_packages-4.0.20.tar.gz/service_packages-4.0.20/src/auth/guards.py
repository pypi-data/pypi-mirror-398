from litestar.connection import ASGIConnection
from litestar.exceptions import HTTPException
from litestar.handlers.base import BaseRouteHandler
from litestar.status_codes import HTTP_403_FORBIDDEN


def is_debug_guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    if not connection.app.debug:
        raise HTTPException(detail="only in debug mode", status_code=HTTP_403_FORBIDDEN)
