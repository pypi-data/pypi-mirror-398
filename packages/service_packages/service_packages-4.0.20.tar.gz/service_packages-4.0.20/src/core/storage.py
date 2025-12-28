from typing import TypeVar

from faststream import FastStream
from faststream.nats import NatsBroker
from litestar import Litestar
import msgspec

from .settings import StorageSettings, settings

T = TypeVar("T")


class Storage:
    def __init__(self, config: StorageSettings):
        self.broker = NatsBroker(servers=config.url)
        self.app = FastStream(self.broker)
        self.settings = config
        self.buckets = {}
        self.is_connected = False

    async def connect(self):
        if not self.is_connected:
            await self.broker.connect()
            for bucket in self.settings.buckets:
                await self.init_bucket(bucket)
            self.is_connected = True

    async def init_bucket(self, name: str):
        self.buckets[name] = await self.broker.key_value(name)

    async def save(self, bucket: str, key: str, data: msgspec.Struct):
        await self.buckets[bucket].put(key, msgspec.json.encode(data))

    async def get(self, bucket: str, key: str, model_type: T) -> T:
        data = await self.buckets[bucket].get(key)
        return msgspec.json.decode(data.value, type=model_type)

    async def delete(self, bucket: str, key: str):
        await self.buckets[bucket].delete(key)

    async def disconnect(self):
        await self.broker.stop()
        self.is_connected = False


async def provide_storage() -> Storage:
    storage = Storage(settings.storage_config)
    await storage.connect()
    return storage


async def close_storage(app: Litestar) -> None:
    storage: Storage = await app.dependencies.get("storage")()
    await storage.disconnect()
