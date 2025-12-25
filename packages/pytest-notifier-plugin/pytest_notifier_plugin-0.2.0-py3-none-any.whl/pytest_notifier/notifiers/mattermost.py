from typing import Any

import httpx

from pytest_notifier.models import TestFailureInfo, TestResults
from pytest_notifier.settings import Settings

from .base import NotifierBase


class MattermostNotifier(NotifierBase):
    """Нотификатор для отправки результатов в Mattermost через Slack-совместимый webhook."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        self.mm = settings.mattermost

    def is_enabled(self) -> bool:
        return self.mm.webhook_url is not None

    def send(self, results: TestResults) -> None:
        """Отправить результаты в Mattermost."""
        all_failures = results.failures + results.errors
        for failure in all_failures:
            payload = self._build_failure_payload(failure)
            self._post_to_webhook(payload)

    def _build_failure_payload(self, failure: TestFailureInfo) -> dict[str, Any]:
        """Создает payload для конкретного упавшего теста."""
        payload = self._build_base_payload()
        payload["text"] = ""  # Все содержимое будет в attachments

        pretext = f"Test failed: **{failure.name}**"
        if self.mm.additional_message:
            pretext += "\n"
            pretext += self.mm.additional_message

        details = [
            f"nodeid: `{failure.nodeid}`",
            f"duration: {failure.duration:.2f}s",
            f"failure:\n```\n{failure.error_message}\n```",
        ]

        if failure.traceback and self.mm.send_traceback:
            details.append("")
            details.append("traceback:")
            details.append(f"```\n{failure.traceback}\n```")

        attachment = {
            "color": "#FF0000",
            "pretext": pretext,
            "text": "\n".join(details),
            "mrkdwn_in": ["pretext", "text"],
        }

        payload["attachments"] = [attachment]

        return payload

    def _build_base_payload(self) -> dict[str, Any]:
        """Создает базовый payload с общими настройками (username, channel, icon)."""
        payload: dict[str, Any] = {}

        if self.mm.username:
            payload["username"] = self.mm.username
        if self.mm.icon_emoji:
            payload["icon_emoji"] = self.mm.icon_emoji
        if self.mm.channel:
            payload["channel"] = self.mm.channel

        return payload

    def _post_to_webhook(self, payload: dict[str, Any]) -> None:
        url = str(self.mm.webhook_url)
        timeout = self.mm.timeout_seconds

        with httpx.Client(timeout=timeout) as client:
            client.post(url, json=payload).raise_for_status()
