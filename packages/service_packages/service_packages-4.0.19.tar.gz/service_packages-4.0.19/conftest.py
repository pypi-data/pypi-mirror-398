import asyncio
from collections.abc import AsyncGenerator
from typing import Any, AsyncGenerator

from advanced_alchemy.base import UUIDAuditBase
from litestar import Litestar
from litestar.di import Provide
import pytest
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from auth import auth_router
from auth.middleware import JWTAuthMiddleware
from core.database import sqlalchemy_plugin
from core.settings import settings
from core.storage import Storage, close_storage, provide_storage
from tests.integrations import TestMailClient


@pytest.fixture(scope="session")
def mail_client():
    return TestMailClient(settings.mail_config)


@pytest.fixture(scope="session")
def application(db_session, mail_client):
    def provide_mail_client():
        return mail_client

    application = Litestar(
        route_handlers=[auth_router],
        on_shutdown=[close_storage],
        plugins=[sqlalchemy_plugin],
        dependencies={
            "mail_client": Provide(provide_mail_client),
            "storage": Provide(provide_storage),
        },
        debug=settings.debug,
        middleware=[JWTAuthMiddleware],
    )
    yield application


@pytest.fixture(scope="session")
def event_loop():
    return asyncio.get_event_loop()


@pytest.fixture(scope="session")
async def db_session() -> AsyncGenerator[AsyncSession, Any]:
    engine = create_async_engine(url=settings.db_url)

    metadata = UUIDAuditBase.registry.metadata
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)

    # create async engine
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

    # clear database
    async with engine.begin() as conn:
        meta = sqlalchemy.MetaData()
        await conn.run_sync(meta.reflect)
        await conn.run_sync(meta.drop_all)


@pytest.fixture(scope="function")
async def storage() -> AsyncGenerator[Storage, Any]:
    storage = await provide_storage()
    await storage.connect()
    yield storage
    await storage.disconnect()
