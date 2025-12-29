"""Файл с конфигурациями логгера."""

import atexit
import contextlib
import fcntl
import logging
import logging.config
import os
import time
from pathlib import Path
from typing import Union

# Базовый конфиг логирования, сохраняем оригинальный формат для ELK
# и настраиваем московское время
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",  # Формат даты без часового пояса
        },
    },
    "handlers": {
        "default": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "INFO",
            "stream": "ext://sys.stdout",
        },
        "file_handler": {
            "class": "logging.FileHandler",
            "level": "INFO",
            "filename": "logs/logger.log",
            "formatter": "standard",
            "encoding": "utf-8",
        },
        "warning_handler": {
            "class": "logging.FileHandler",
            "level": "WARNING",
            "filename": "logs/warnings.log",
            "formatter": "standard",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "": {
            "handlers": ["default", "file_handler", "warning_handler"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


class SafeFileHandler(logging.FileHandler):
    """FileHandler с блокировкой файла для безопасной записи в многопроцессной среде."""

    def __init__(
            self,
            filename: str,
            mode: str = "a",
            encoding: Union[str, None] = None,  # noqa: FA100
            *,
            delay: bool = False,
    ) -> None:
        """Инициализация класса."""
        # Создаем директорию для лога, если она не существует
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        super().__init__(filename, mode, encoding, delay)

    def emit(self, record: logging.LogRecord) -> None:
        """Безопасная запись с файловой блокировкой."""
        if self.stream is None:
            self.stream = self._open()

        try:
            fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX)
            super().emit(record)
            self.stream.flush()
        except Exception:  # noqa: BLE001
            self.handleError(record)
        finally:
            if self.stream:
                with contextlib.suppress(Exception):
                    fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN)


def get_logger_handlers(logger_name: str, log_config: dict) -> tuple[SafeFileHandler, SafeFileHandler]:
    """
    Создает и возвращает безопасные обработчики для логгера.

    Args:
        logger_name: Имя логгера (используется для имени файла)
        log_config: Конфигурация логирования

    Returns:
        tuple: (file_handler, warning_handler) - безопасные обработчики

    """
    # Директория для логов
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Пути к файлам
    log_file = str(log_dir / f"{logger_name}.log")
    warning_file = str(log_dir / "warnings.log")

    # Устанавливаем московское время для логов
    os.environ["TZ"] = "Europe/Moscow"
    with contextlib.suppress(AttributeError):
        time.tzset()

    # Формат логов
    format_str = log_config["formatters"]["standard"]["format"]
    date_fmt = log_config["formatters"]["standard"].get("datefmt", "%Y-%m-%d %H:%M:%S %z")
    formatter = logging.Formatter(format_str, date_fmt)

    # Создаем безопасные обработчики
    safe_file_handler = SafeFileHandler(
        filename=log_file,
        encoding="utf-8",
    )
    safe_file_handler.setLevel(logging.INFO)
    safe_file_handler.setFormatter(formatter)

    warning_handler = SafeFileHandler(
        filename=warning_file,
        encoding="utf-8",
    )
    warning_handler.setLevel(logging.WARNING)
    warning_handler.setFormatter(formatter)

    return safe_file_handler, warning_handler


def close_handlers() -> None:
    """Закрывает все обработчики логов."""
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        with contextlib.suppress(Exception):
            handler.close()


# Регистрируем функцию для корректного закрытия файлов логов
atexit.register(close_handlers)
