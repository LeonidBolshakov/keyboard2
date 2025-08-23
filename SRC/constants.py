"""
constants.py — неизменяемые константы.

Назначение:
- Хранит ключи конфигурации, значения по умолчанию, формат логов.
- Предоставляет «только чтение» через объект C, чтобы избежать случайной перезаписи.

Использование:
    from SRC.constants import C
    level_name = C.CONSOLE_LOG_LEVEL_DEF
"""

import logging
from pathlib import Path


class _Const:
    """
    Контейнер констант «только для чтения».

    Почему не модульные переменные:
    - Нужна защита от присваивания (AttributeError при попытке изменения).
    - Явное пространство имён C.* повышает читабельность.
    """

    # --- Ключи конфигурации / имена переменных окружения
    CONSOLE_LOG_LEVEL: str = "console_log_level"
    FILE_LOG_LEVEL: str = "file_log_level_info"  # сохранён исходный ключ
    FILE_LOG_PATH: str = "file_log_path"  # исправленный ключ

    # --- Значения по умолчанию
    CONSOLE_LOG_LEVEL_DEF: str = "INFO"
    FILE_LOG_LEVEL_DEF: str = "DEBUG"
    FILE_LOG_DIR_DEF: str = r"C:\TEMP"
    FILE_LOG_FILENAME_DEF: str = "keyboard2.log"
    FILE_LOG_PATH_DEF: str = str(Path(FILE_LOG_DIR_DEF) / FILE_LOG_FILENAME_DEF)

    # --- Формат сообщений
    LOG_FORMAT: str = "%(asctime)s %(levelname)s %(name)s %(message)s"

    # --- Ротация файла
    ROTATING_MAX_BYTES: int = 10_000
    ROTATING_BACKUP_COUNT: int = 5

    # --- Преобразование строкового уровня в код logging
    CONVERT_LOGGING_NAME_TO_CODE: dict[str, int] = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    # --- Сообщение single
    SINGLE_TEXT = "Экземпляр программы уже работает"

    # --- Тексты ошибок
    TEXT_ERROR_GET_VAR_1 = "Метод get_var класса Variables.\nПервый параметр {name} имеет тип отличный от str"
    TEXT_ERROR_GET_VAR_2 = "Метод get_var класса Variables.\nВторой параметр {default} имеет тип отличный от str"
    TEXT_ERROR_LOG_LEVEL_NAME = "Некорректное значение уровня для {env_name}: {name}"
    TEXT_ERROR_REGISTER_HOTKEY = (
        "Отказано в регистрации горячей клавиши  hk_id={hk_id} mods={mods} vk={vk}"
    )
    TEXT_ERROR_START_APP = "Фатальная ошибка на старте приложения {e}"
    TEXT_ERROR_TUNE_LOGGER = "Настройка логирования завершилась ошибкой {e}"

    def __setattr__(self, key, value):
        """
        Блокирует изменение констант во время исполнения.

        Любая попытка: C.SOME = ... -> AttributeError.
        """
        raise AttributeError(f"Нельзя менять константу {key}")


# Публичный объект с константами (read-only интерфейс)
C = _Const()
