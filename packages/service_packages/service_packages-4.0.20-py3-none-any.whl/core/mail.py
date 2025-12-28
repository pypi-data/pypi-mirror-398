from email.message import EmailMessage
import smtplib

from .settings import MailSettings, settings


class MailClient:
    def __init__(self, config: MailSettings):
        self.settings = config

    def send(self, recipients: list[str], subject: str, body: str):
        msg = EmailMessage()
        msg.set_content(body)
        server = smtplib.SMTP(self.settings.host, self.settings.port, timeout=5)
        server.starttls()
        server.login(self.settings.login, self.settings.password)

        msg = EmailMessage()
        msg["Subject"] = subject
        msg.set_content(body)
        msg["From"] = self.settings.login

        for recipient in recipients:
            msg["To"] = recipient
            server.send_message(msg)

        server.quit()


async def provide_mail_client():
    return MailClient(settings.mail_config)
