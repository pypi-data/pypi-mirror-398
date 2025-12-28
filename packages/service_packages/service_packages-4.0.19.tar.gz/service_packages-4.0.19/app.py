from litestar import Litestar
from litestar.di import Provide

from auth.api import auth_router
from auth.middleware import JWTAuthMiddleware
from auth.plugin import AuthPlugin
from core.database import sqlalchemy_plugin
from core.mail import provide_mail_client
from core.openapi import openapi_config
from core.settings import settings
from core.storage import close_storage, provide_storage


def create_app():
    app = Litestar(
        route_handlers=[auth_router],
        middleware=[JWTAuthMiddleware],
        plugins=[sqlalchemy_plugin, AuthPlugin()],
        openapi_config=openapi_config,
        debug=settings.debug,
        on_shutdown=[close_storage],
        dependencies={
            "storage": Provide(provide_storage),
            "mail_client": Provide(provide_mail_client),
        },
    )
    return app
