from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from litestar.openapi.spec import Components, SecurityScheme

from .settings import settings

openapi_config = OpenAPIConfig(
    components=[
        Components(
            security_schemes={
                "JWT": SecurityScheme(
                    type="http",
                    scheme="Bearer",
                    name="Authorization",
                    security_scheme_in="cookie",
                    bearer_format="JWT",
                    description="Authorization",
                )
            }
        )
    ],
    title=settings.open_api_config.title,
    version=settings.open_api_config.version,
    path=settings.open_api_config.path,
    render_plugins=[ScalarRenderPlugin()],
)
