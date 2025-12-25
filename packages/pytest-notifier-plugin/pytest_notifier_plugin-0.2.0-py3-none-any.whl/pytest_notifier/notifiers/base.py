from abc import ABC, abstractmethod

from pytest_notifier.models import TestResults
from pytest_notifier.settings import Settings


class NotifierBase(ABC):
    """Базовый класс для всех нотификаторов."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @abstractmethod
    def send(self, results: TestResults) -> None:
        """Отправить уведомление о результатах тестов."""
        pass

    @abstractmethod
    def is_enabled(self) -> bool:
        """Проверить, включён ли нотификатор и настроен ли корректно."""
        pass
