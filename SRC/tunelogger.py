from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler

from SRC.get_variable import Variables
from constants import C

logger = logging.getLogger(__name__)


class TuneLogger:
    """Настройка логирования: консоль + файл с ротацией, уровни из окружения."""

    def __init__(self):
        self.variables = Variables()
        self.console_handler = logging.StreamHandler()
        self.file_handler = self._create_file_handler()

    def setup_logging(self) -> None:
        """Полная настройка root-логгера."""
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

    def _set_log_format(self) -> None:
        """Установка формата логов"""
        fmt = logging.Formatter(C.LOG_FORMAT)

        self.console_handler.setFormatter(fmt)
        self.file_handler.setFormatter(fmt)

    def _create_file_handler(self) -> RotatingFileHandler:
        """Создать файловый обработчик. Если указан каталог — использовать имя по умолчанию."""
        # читаем значение в окружении, если его нет - дефолт — полноценный путь
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

    def add_handlers(self) -> None:
        """Добавить текущие обработчики к root (без очистки)."""
        root = logging.getLogger()
        root.addHandler(self.console_handler)
        root.addHandler(self.file_handler)

    @staticmethod
    def _remove_logging() -> None:
        """Удалить все обработчики у root."""
        root = logging.getLogger()
        for h in root.handlers[:]:
            root.removeHandler(h)

    def _get_log_level(self, env_name: str, default_name: str) -> int:
        """Преобразовать строковый уровень из окружения в код logging.*"""
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
