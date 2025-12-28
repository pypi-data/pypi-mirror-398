from core.mail import MailClient, MailSettings


class TestMailClient(MailClient):
    def __init__(self, settings: MailSettings):
        super().__init__(settings)
        self.messages = []

    def send(self, recipients: list[str], subject: str, body: str):
        self.messages.append((recipients, subject, body))

    def reset(self):
        self.messages = []
