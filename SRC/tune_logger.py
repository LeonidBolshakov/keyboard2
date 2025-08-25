"""
Модуль tune_logger.py


Назначение
---------
Настройка логирования приложения: вывод в консоль и запись в файл с ротацией.
Параметры (уровни логирования, путь к файлу) берутся из переменных окружения,
которые подгружаются с помощью класса Variables.


Состав
------
- Класс `TuneLogger` — инкапсулирует создание обработчиков логов, настройку
уровней и формата.
- Поддерживает:
* очистку старых обработчиков и повторную настройку (`setup_logging`),
* добавление только своих обработчиков (`add_handlers`),
* настройку уровней и формата отдельно для консоли и файла,
* создание файлового обработчика с ротацией (RotatingFileHandler).


Примечания
---------
- Если в окружении указан каталог без имени файла, используется имя по умолчанию.
- При первом запуске файл создаётся в режиме записи, иначе открывается в режиме
добавления.
"""

from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler

from SRC.get_variable import Variables
from SRC.constants import C

logger = logging.getLogger(__name__)


class TuneLogger:
    """Класс для настройки логирования: консоль + файл с ротацией.


    Методы
    ------
    setup_logging() -> None
    Полностью настраивает root-логгер: очищает старые обработчики,
    добавляет новые, выставляет уровни и формат.


    _add_handlers() -> None
    Добавляет обработчики в root-логгер без очистки.


    _create_file_handler() -> RotatingFileHandler
    Внутренний метод: создаёт файловый обработчик с ротацией.
    Учитывает, является ли путь каталогом или файлом.


    _get_log_level(env_name: str, default_name: str) -> int
    Внутренний метод: возвращает числовой код уровня логирования
    (logging.DEBUG, INFO и т. д.) по имени из переменных окружения.
    """

    def __init__(self):
        self.variables = Variables()
        self.console_handler = logging.StreamHandler()
        self.file_handler = self._create_file_handler()

    def setup_logging(self) -> None:
        """Полная настройка головного логгера: очистка, добавление и настройка обработчиков."""
        self._remove_logging()
        self._add_handlers()
        self._set_log_levels()
        self._set_log_format()

    def _add_handlers(self) -> None:
        """Добавление обработчиков в головной логгер"""
        root = logging.getLogger()

        root.addHandler(self.console_handler)
        root.addHandler(self.file_handler)

    def _set_log_levels(self) -> None:
        """Установка уровней логирования отдельно для консоли и файла"""
        console_log_level = self._get_log_level(
            C.CONSOLE_LOG_LEVEL, C.CONSOLE_LOG_LEVEL_DEF
        )
        file_log_level = self._get_log_level(C.FILE_LOG_LEVEL, C.FILE_LOG_LEVEL_DEF)

        self.console_handler.setLevel(console_log_level)
        self.file_handler.setLevel(file_log_level)

        logging.getLogger("PyQt6.uic").setLevel(logging.WARNING)

        root = logging.getLogger()
        root.setLevel(min(console_log_level, file_log_level))

    def _set_log_format(self) -> None:
        """Установка формата логов"""
        fmt = logging.Formatter(C.LOG_FORMAT)

        self.console_handler.setFormatter(fmt)
        self.file_handler.setFormatter(fmt)

    def _create_file_handler(self) -> RotatingFileHandler:
        """Создать файловый обработчик с ротацией."""
        # читаем значение пути файла журнала в окружении, если его нет - дефолт — полноценный путь
        path_str = self.variables.get_var(C.FILE_LOG_PATH, C.FILE_LOG_PATH_DEF)
        p = Path(path_str)

        # Случай 1: путь заканчивается на слэш и не содержит имени файла
        if not p.name:
            p = p / C.FILE_LOG_FILENAME_DEF
        # Случай 2: путь указывает на реально существующую папку
        elif p.is_dir():
            p = p / C.FILE_LOG_FILENAME_DEF

        p.parent.mkdir(parents=True, exist_ok=True)

        mode = "w" if (not p.exists() or p.stat().st_size == 0) else "a"

        return RotatingFileHandler(
            filename=str(p),
            mode=mode,
            maxBytes=C.ROTATING_MAX_BYTES,
            backupCount=C.ROTATING_BACKUP_COUNT,
            encoding="utf-8-sig",
            delay=True,
        )

    @staticmethod
    def _remove_logging() -> None:
        """Удалить все обработчики у головного логгера."""
        root = logging.getLogger()
        for h in root.handlers[:]:
            root.removeHandler(h)
            try:
                h.close()
            except Exception:
                pass

    def _get_log_level(self, env_name: str, default_name: str) -> int:
        """
        Возвращает числовой уровень логирования по имени уровня логирования.
        Имя уровня логирования задаётся в окружении.


        :param env_name:        Имя переменной окружения, содержащей имя уровня логирования.
        :param default_name:    Имя уровня логирования, задаваемое по умолчанию.
                                Применяется если нет значения для переменной окружения с имением,
                                заданным предыдущим параметром.
        :return:                Возвращает числовое значение уровня логирования.
                                Если по заданным параметром числовое значение найти не удалось,
                                возвращается - logging.DEBUG
        """
        name = self.variables.get_var(env_name, default_name)
        if not isinstance(name, str):
            try:
                name = str(name)
            except Exception:
                logger.warning(
                    C.TEXT_ERROR_LOG_LEVEL_NAME.format(env_name=env_name, name=name)
                )
                name = default_name

        return C.CONVERT_LOGGING_NAME_TO_CODE.get(name.upper(), logging.DEBUG)