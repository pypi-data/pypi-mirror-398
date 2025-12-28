from faker import Faker
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory
from polyfactory.fields import Use

from .models import PermissionModel, RoleModel, UserModel

faker = Faker()


class UserFactory(SQLAlchemyFactory[UserModel]):
    email = Use(faker.unique.email)


class RoleFactory(SQLAlchemyFactory[RoleModel]):
    name = Use(faker.unique.word)


class PermissionFactory(SQLAlchemyFactory[PermissionModel]):
    name = Use(faker.unique.word)
