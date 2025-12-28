from pathlib import Path

import click
from click import Group
from litestar.plugins import CLIPlugin
import yaml

from core.cli import coro
from core.database import session_maker
from core.mail import MailClient
from core.settings import settings

from .loaders import AuthLoader
from .services import provide_permission_service, provide_role_service, provide_user_service


class AuthPlugin(CLIPlugin):
    def on_cli_init(self, cli: Group) -> None:
        @cli.group(help="Manage auth, load data with ``load`` command")
        @click.version_option(prog_name="auth")
        def auth(): ...

        @auth.command(help="load auth data")
        @coro
        async def load():
            async with session_maker() as session:
                click.echo("Loading auth data... ")
                loader = AuthLoader(
                    user_service=await provide_user_service(session),
                    role_service=await provide_role_service(session),
                    permission_service=await provide_permission_service(session),
                )

                with open(f"{Path(__file__).parent.resolve()}/fixtures.yaml") as f:
                    data = yaml.safe_load(f)
                    await loader.load(data)

        @auth.command(help="load auth data")
        @coro
        async def clear():
            async with session_maker() as session:
                user_service = await provide_user_service(session)
                await user_service.delete_where()
                click.echo("Clear auth data")

        @auth.command(help="Send test mail")
        @click.argument("recipient")
        def send_mail(recipient):
            mail_controller = MailClient(settings.mail_config)
            mail_controller.send([recipient], "test", "test")
