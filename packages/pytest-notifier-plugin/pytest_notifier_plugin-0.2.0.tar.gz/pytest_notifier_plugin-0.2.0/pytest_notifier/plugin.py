import contextlib

import pytest

from .models import TestFailureInfo, TestResults
from .notifiers import NOTIFIER_REGISTRY, NotifierBase
from .settings import Settings


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Хук pytest: отправляет сводку результатов во все активные каналы."""
    settings = Settings()
    results = extract_test_results(session, exitstatus)

    # Отправляем уведомления только если есть упавшие тесты или ошибки
    if results.failed == 0 and results.error == 0:
        return

    notifiers = get_active_notifiers(settings)

    for notifier in notifiers:
        with contextlib.suppress(Exception):
            notifier.send(results)


def extract_test_results(session: pytest.Session, exitstatus: int) -> TestResults:
    """Извлекает результаты из pytest.Session в независимую структуру."""
    tr = session.config.pluginmanager.get_plugin("terminalreporter")

    passed = failed = error = skipped = xfailed = xpassed = 0
    collected = getattr(session, "testscollected", None)
    failures: list[TestFailureInfo] = []
    errors: list[TestFailureInfo] = []

    if tr is not None:
        stats = getattr(tr, "stats", {})
        passed = len(stats.get("passed", []))
        failed = len(stats.get("failed", []))
        error = len(stats.get("error", []))
        skipped = len(stats.get("skipped", []))
        xfailed = len(stats.get("xfailed", []))
        xpassed = len(stats.get("xpassed", []))

        if collected is None:
            collected = getattr(tr, "_numcollected", 0)

        # Извлекаем детальную информацию об упавших тестах
        failures.extend(
            extract_failure_info(report) for report in stats.get("failed", [])
        )

        # Извлекаем детальную информацию о тестах с ошибками
        errors.extend(extract_failure_info(report) for report in stats.get("error", []))

    if collected is None:
        collected = passed + failed + error + skipped + xfailed + xpassed

    exitstatus_text = exitstatus_to_text(exitstatus)

    return TestResults(
        collected=collected,
        passed=passed,
        failed=failed,
        error=error,
        skipped=skipped,
        xfailed=xfailed,
        xpassed=xpassed,
        exitstatus=exitstatus,
        exitstatus_text=exitstatus_text,
        failures=failures,
        errors=errors,
    )


def get_active_notifiers(settings: Settings) -> list[NotifierBase]:
    """Возвращает список активных нотификаторов на основе флагов destinations."""
    notifiers = []

    for destination, notifier_class in NOTIFIER_REGISTRY.items():
        if settings.destinations & destination:
            notifier = notifier_class(settings)
            if notifier.is_enabled():
                notifiers.append(notifier)

    return notifiers


def extract_failure_info(report) -> TestFailureInfo:
    """Извлекает информацию об ошибке из TestReport."""
    file_path, line, test_name = report.location
    error_message = get_short_error_message(report)
    traceback = getattr(report, "longreprtext", None)

    return TestFailureInfo(
        nodeid=report.nodeid,
        name=test_name,
        file_path=file_path,
        error_message=error_message,
        traceback=traceback,
        duration=getattr(report, "duration", 0.0),
    )


def get_short_error_message(report) -> str:
    """Извлекает краткое сообщение об ошибке из отчёта."""
    longrepr = getattr(report, "longrepr", None)

    if longrepr is None:
        return "Unknown error"

    # Если longrepr - строка, возвращаем её (обрезаем если длинная)
    if isinstance(longrepr, str):
        return longrepr[:200]

    # Если longrepr - объект, пытаемся извлечь reprcrash
    reprcrash = getattr(longrepr, "reprcrash", None)
    if reprcrash:
        message = getattr(reprcrash, "message", "")
        if message:
            return message[:200]

    # Fallback: берём первую строку из longreprtext
    longreprtext = getattr(report, "longreprtext", "")
    if longreprtext:
        first_line = longreprtext.split("\n")[0]
        return first_line[:200]

    return "Unknown error"


def exitstatus_to_text(exitstatus: int) -> str:
    """Преобразует код выхода pytest в текст."""
    try:
        code = pytest.ExitCode(exitstatus)
        return code.name
    except Exception:
        return str(exitstatus)
