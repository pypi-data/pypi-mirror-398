from pydantic import Field
from pydantic_settings import BaseSettings


class StorageSettings(BaseSettings):
    url: str = Field(default="nats://localhost:4222")
    buckets: list[str] = Field()

    class Config:
        env_prefix = "STORAGE_"


class MailSettings(BaseSettings):
    host: str = Field(default="smtp.yandex.com")
    port: int = Field(default=587)
    login: str = Field(default="info@service-laboratory.online")
    password: str = Field(default="superPassword")

    class Config:
        env_prefix = "MAIL_"


class OpenApiSettings(BaseSettings):
    title: str = Field(deafult="title")
    version: str = Field(deafult="0.1.2")
    path: str = Field(deafult="/api/docs")

    class Config:
        env_prefix = "OPEN_API_"


class Settings(BaseSettings):
    debug: bool = Field(default=False)
    jwt_secret: str = Field(default="secret_for_jwt")

    # database config
    db_url: str = Field(default="postgresql+asyncpg://user:password@localhost:5432/db")
    db_create_all: bool = Field(default=False)

    # services config
    open_api_config: OpenApiSettings = Field(default_factory=OpenApiSettings)
    mail_config: MailSettings = Field(default_factory=MailSettings)
    storage_config: StorageSettings = Field(default_factory=StorageSettings)


settings = Settings()
