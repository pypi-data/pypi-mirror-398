"""Основные вспомогательные функции для проекта."""

import copy
import inspect
import logging.config
from pathlib import Path

from dotenv import dotenv_values

from mpstats.configs.logger_settings import LOGGING_CONFIG, get_logger_handlers


def setup_logger() -> logging.Logger:
    """
    Настраивает и возвращает логгер для текущего модуля.

    Обеспечивает безопасное логирование в многопроцессной среде.

    Returns:
        logging.Logger: Настроенный логгер для модуля вызывающей стороны

    """
    # Получаем имя файла вызывающей стороны
    caller_filename = inspect.stack()[1].filename
    logger_name = Path(caller_filename).stem

    # Проверяем, не настроен ли уже логгер
    logger = logging.getLogger(logger_name)
    if logger.handlers:
        return logger

    # Создаем копию конфигурации, чтобы не изменять оригинал
    log_config = copy.deepcopy(LOGGING_CONFIG)

    # Применяем базовую конфигурацию
    logging.config.dictConfig(log_config)

    # Получаем безопасные обработчики для файлов
    file_handler, warning_handler = get_logger_handlers(logger_name, log_config)

    # Заменяем стандартные обработчики на безопасные
    logger = logging.getLogger(logger_name)
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.FileHandler) and not hasattr(handler, "safe_handler_flag"):
            logger.removeHandler(handler)
            if handler.level == logging.WARNING:
                logger.addHandler(warning_handler)
            else:
                logger.addHandler(file_handler)

    return logger


def load_env_config() -> dict:
    """Загрузка секретных переменных окружения."""
    path = Path.cwd()
    dotenv_path = path / ".env"
    config = dotenv_values(dotenv_path=dotenv_path)
    return config
