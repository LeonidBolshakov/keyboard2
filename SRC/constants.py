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

from PyQt6.QtGui import QColor


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

    # --- Сообщение об удачной загрузке программы
    COLOR_MESSAGE_START_PROGRAM = QColor("green")
    HOTKEY_BEGIN_DIALOGUE = "scroll lock"  # Клавиша вызова окна замены регистров
    TEXT_MESSAGE_START_PROGRAM = (
        "Запущена программа замены регистра выделенного текста. Горячая клавиша {key}"
    )
    TIME_MESSAGE_START_PROGRAM = (
        0.3  # Время высвечивания сообщения о запуске программы (в секундах)
    )

    # --- Сообщения логирования
    LOGGER_TEXT_CHANGE = "Заменённый текст *{text}*"
    LOGGER_TEXT_ERROR_READ_CLIPBOARD = "Из Clipboard считан пустой текст"
    LOGGER_TEXT_LOAD_PROGRAM = "Программа загружена"
    LOGGER_TEXT_NO_IN_CLIPBOARD = (
        "Выделенный текст не попал в буфер обмена. Время ожидания - {time_delay}"
    )
    LOGGER_TEXT_ORIGINAL = "Текст пользователя *{text}*"
    LOGGER_TEXT_RESTORED_CLIPBOARD = "Текст +*{clipboard_text}*+ возвращён буфер обмена"
    LOGGER_TEXT_START_DIALOGUE = "Начало диалога. Окно - {title}"
    LOGGER_TEXT_STOP_DIALOGUE = "Диалог завершён"
    LOGGER_TEXT_UNLOAD_PROGRAM = "Программа выгружена из памяти"

    # --- Работа с буфером обмена
    MAX_CLIPBOARD_READS = 2  # максимально число считываний буфера обмена
    TIME_DELAY_CTRL_C = 0.1  # Задержка, в секундах, после нажатия Ctrl+c
    TIME_DELAY_CTRL_V = 0.1  # Задержка, в секундах, после нажатия Ctrl+v

    # --- Пути программ
    UI_PATH_FROM_EXE = r"_internal\dialogue.ui"

    # --- Настройки кнопок
    MIN_WIDTH_BUTTON = 170  # Минимальная ширина первых двух кнопок
    QSS_BUTTON = "font-weight: bold; font-size: 12pt; "
    QSS_NO = "color: darkblue;"
    QSS_TEXT = "color: mediumblue;"  # Силь текстовых полей диалога
    QSS_YES = "color: blue;"
    TEXT_CANCEL_BUTTON = "Выгрузить программу\nНажми 3"
    TEXT_NO_BUTTON = "Не заменять\nНажми 2/Esc"
    TEXT_YES_BUTTON = "Заменить\nНажми 1"

    # --- Сообщение single
    SINGLE_TEXT = "Экземпляр программы уже работает"

    # --- Тексты ошибок
    TEXT_CRITICAL_ERROR = (
        "Не предусмотренная программой команда закрытия диалога command={command}"
    )
    TEXT_ERROR_CONNECT = (
        "Ошибка при назначении обработчиков кнопкам или другим объектам {e}"
    )
    TEXT_ERROR_CUSTOM_UI = "Ошибка при настройке пользовательских интерфейсов {e}"
    TEXT_ERROR_GET_VAR_1 = "Метод get_var класса Variables.\nПервый параметр {name} имеет тип отличный от str"
    TEXT_ERROR_GET_VAR_2 = "Метод get_var класса Variables.\nВторой параметр {default} имеет тип отличный от str"
    TEXT_ERROR_INIT_BUTTON = "Ошибка инициализации кнопок всплывающего окна {e}"
    TEXT_ERROR_LOAD_UI = (
        "Ошибка загрузки UI (Описаний окна, подготовленных QtDesigner - {e}"
    )
    TEXT_ERROR_LOG_LEVEL_NAME = "Некорректное значение уровня для {env_name}: {name}"
    TEXT_ERROR_PROCESSING_CLIPBOARD = " Ошибка при чтении из буфера обмена {e}"
    TEXT_ERROR_REGISTER_HOTKEY = (
        "Отказано в регистрации горячей клавиши  hk_id={hk_id} mods={mods} vk={vk}"
    )
    TEXT_ERROR_REPLACE_TEXT = "Ошибка при формировании/записи заменяющего текста"
    TEXT_ERROR_START_APP = "Фатальная ошибка на старте приложения {e}"
    TEXT_ERROR_PUT_ORIGINAL_TEXT = (
        "Ошибка при отображении в сплывающее окно текста пользователя {e}"
    )
    TEXT_ERROR_SHOW_REPLACEMENTS_TEXT = (
        "Ошибка при формировании/отображении замещающего текст {e}"
    )
    TEXT_ERROR_TUNE_LOGGER = "Настройка логирования завершилась ошибкой {e}"
    TEXT_WINDOW_NOT_FOUND = "Название окна неизвестно"

    def __setattr__(self, key, value):
        """
        Блокирует изменение констант во время исполнения.

        Любая попытка: C.SOME = ... -> AttributeError.
        """
        raise AttributeError(f"Нельзя менять константу {key}")


# Публичный объект с константами (read-only интерфейс)
C = _Const()