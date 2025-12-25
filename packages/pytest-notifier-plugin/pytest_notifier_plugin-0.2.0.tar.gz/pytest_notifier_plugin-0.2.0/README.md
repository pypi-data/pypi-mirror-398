# pytest-notifier-plugin

Плагин для pytest, который отправляет уведомления об упавших тестах в различные каналы связи (Console, Mattermost, Telegram).

## Особенности

- Отправка уведомлений при падении тестов.
- Поддержка нескольких каналов одновременно.
- Гибкая конфигурация через переменные окружения или `.env` файлы.
- Детальная информация об ошибках, включая traceback.
- Возможность добавлять произвольные сообщения в конец нотификаций (для Telegram и Mattermost).

## Установка

Для использования плагина, убедитесь, что он доступен в вашем окружении. Если это локальный пакет:

```bash
pip install pytest-notifier-plugin
```

## Использование

Плагин активируется автоматически при запуске `pytest`, если он установлен.

## Конфигурация

Настройка производится через переменные окружения. Префикс для всех переменных: `PYTEST_NOTIFIER_`.

### Основные настройки

`PYTEST_NOTIFIER_DESTINATIONS` - главная переменная, указывающая на то куда отправлять уведомления (битовая маска).

#### Расчет значения DESTINATIONS

Значение формируется суммированием флагов необходимых каналов:

| Канал          | Значение флага |
|----------------|:--------------:|
| **Console**    | `1`            |
| **Mattermost** | `2`            |
| **Telegram**   | `4`            |

**Примеры комбинаций:**

| Комбинация            | Расчет    | Итоговое значение |
|-----------------------|-----------|:-----------------:|
| Только Console        | 1         | `1`               |
| Только Mattermost     | 2         | `2`               |
| Только Telegram       | 4         | `4`               |
| Console + Mattermost  | 1 + 2     | `3`               |
| Console + Telegram    | 1 + 4     | `5`               |
| Mattermost + Telegram | 2 + 4     | `6`               |
| **Все каналы**        | 1 + 2 + 4 | `7`               |

### Mattermost

| Переменная                                      | Описание                                                                   |
|-------------------------------------------------|----------------------------------------------------------------------------|
| `PYTEST_NOTIFIER_MATTERMOST__WEBHOOK_URL`       | URL вебхука для отправки сообщений.                                        |
| `PYTEST_NOTIFIER_MATTERMOST__USERNAME`          | Имя бота.                                                                  |
| `PYTEST_NOTIFIER_MATTERMOST__CHANNEL`           | Канал, куда будут отправляться сообщения                                   |
| `PYTEST_NOTIFIER_MATTERMOST__ICON_EMOJI`        | Emoji для иконки бота (опционально, например `:ghost:`).                   |
| `PYTEST_NOTIFIER_MATTERMOST__TIMEOUT_SECONDS`   | Таймаут запроса в секундах. (По умолчанию: 10 сек.)                        |
| `PYTEST_NOTIFIER_MATTERMOST__SEND_TRACEBACK`    | Отправлять ли traceback ошибки. `true` или `false`. (По умолчанию: `true`) |
| `PYTEST_NOTIFIER_MATTERMOST__ADDITIONAL_MESSAGE`| Дополнительное сообщение, которое будет добавлено в конец нотификации.     |

### Telegram

| Переменная                                    | Описание                                                                   |
|-----------------------------------------------|----------------------------------------------------------------------------|
| `PYTEST_NOTIFIER_TELEGRAM__BOT_TOKEN`         | Токен вашего бота.                                                         |
| `PYTEST_NOTIFIER_TELEGRAM__CHAT_ID`           | ID чата (или канала), куда отправлять сообщения.                           |
| `PYTEST_NOTIFIER_TELEGRAM__TIMEOUT_SECONDS`   | Таймаут запроса в секундах. (По умолчанию: 10.0)                           |
| `PYTEST_NOTIFIER_TELEGRAM__SEND_TRACEBACK`    | Отправлять ли traceback ошибки. `true` или `false`. (По умолчанию: `true`) |
| `PYTEST_NOTIFIER_TELEGRAM__ADDITIONAL_MESSAGE`| Дополнительное сообщение, которое будет добавлено в конец нотификации.     |

### Пример `.env` файла

```ini
# Включить отправку в Mattermost и Telegram (2 + 4 = 6)
PYTEST_NOTIFIER_DESTINATIONS=6

# Mattermost
PYTEST_NOTIFIER_MATTERMOST__WEBHOOK_URL=https://mattermost.example.com/hooks/xxx
PYTEST_NOTIFIER_MATTERMOST__USERNAME=TestBot
PYTEST_NOTIFIER_MATTERMOST__CHANNEL=qa-alerts
PYTEST_NOTIFIER_MATTERMOST__ADDITIONAL_MESSAGE="Документация: https://docs.example.com"

# Telegram
PYTEST_NOTIFIER_TELEGRAM__BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
PYTEST_NOTIFIER_TELEGRAM__CHAT_ID=-1001234567890
PYTEST_NOTIFIER_TELEGRAM__SEND_TRACEBACK=false
PYTEST_NOTIFIER_TELEGRAM__ADDITIONAL_MESSAGE="Свяжитесь с командой QA для подробностей"
```

## Разработка

Для управления зависмостями проекта используется пакетный менеджер [uv](https://docs.astral.sh/uv/). Для установки python зависимостей выполните команду:

```bash
uv sync
```

После внесения изменений нужно прогнать линтеры:

```bash
uv run ruff check
uv run ty check
```
