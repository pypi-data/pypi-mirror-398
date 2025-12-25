import httpx

from pytest_notifier.models import TestResults
from pytest_notifier.settings import Settings

from .base import NotifierBase


class TelegramNotifier(NotifierBase):
    """Нотификатор для отправки результатов в Telegram через Bot API."""

    BASE_URL = "https://api.telegram.org/bot"

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        self.tg = settings.telegram

    def is_enabled(self) -> bool:
        return self.tg.bot_token is not None and self.tg.chat_id is not None

    def send(self, results: TestResults) -> None:
        all_failures = results.failures + results.errors
        for _, failure in enumerate(all_failures, 1):
            lines = [
                f"Test failed: *{failure.name}*",
                "",
                f"nodeid: `{failure.nodeid}`",
                f"duration: {failure.duration:.2f}s",
                "failure:",
                f"```\n{failure.error_message}\n```",
            ]

            if failure.traceback and self.settings.telegram.send_traceback:
                lines.extend([
                    "",
                    "traceback:",
                    f"```\n{failure.traceback}\n```",
                ])

            if self.tg.additional_message:
                lines.extend([
                    "",
                    self.tg.additional_message,
                ])

            message = "\n".join(lines)
            self._send_message(message)

    def _send_message(self, text: str) -> None:
        bot_token = self.tg.bot_token.get_secret_value()  # type: ignore
        url = f"{self.BASE_URL}{bot_token}/sendMessage"

        payload = {
            "chat_id": self.tg.chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }

        with httpx.Client(timeout=self.tg.timeout_seconds) as client:
            client.post(url, json=payload).raise_for_status()
