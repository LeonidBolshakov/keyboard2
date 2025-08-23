"""
Точка входа приложения.

Назначение
---------.
Инициализирует логирование, запускает основное Qt‑приложение и корректно
обрабатывает исключения на верхнем уровне, возвращая код завершения процессу.

Состав модуля
-------------
- Импортирует настройку логирования (`TuneLogger`).
- Импортирует класс приложения (`MainApp`).
- Определяет функцию `main()` как оболочку запуска с обработкой ошибок.
- Вызывает запуск при исполнении файла как скрипта.

Примечание
---------
`MainApp().main_app()` возвращает целочисленный код выхода Qt‑цикла (результат
`QApplication.exec()`), который далее используется как код завершения процесса.
"""

# ---- Точка входа
import sys
from logging import getLogger

logger = getLogger(__name__)

from SRC.tune_logger import TuneLogger
from SRC.app import MainApp
from SRC.constants import C


def main() -> int:
    """Запускает приложение с настройкой логирования и обработкой ошибок.

    Возвращает
    -----------
    int
        Код завершения процесса (обычно код выхода Qt‑цикла событий).
    """
    try:
        tune_logger = TuneLogger()
        tune_logger.setup_logging()
    except Exception as e:
        # Если логгер не настроился, печатаем сообщение и продолжаем запуск
        print(C.TEXT_ERROR_TUNE_LOGGER.format(e=e))
    try:
        app_code = MainApp().main_app()
    except SystemExit as e:
        # Корректная передача кода выхода, если где‑то вызван SystemExit
        sys.exit(int(e.code) if hasattr(e, "code") else 0)
    except Exception as e:
        # Записываем в лог не перехваченное исключение и выходим с кодом 1
        logger.exception(C.TEXT_ERROR_TUNE_LOGGER.format(e=e))
        sys.exit(1)
    # Возвращаем код, чтобы sys.exit(main()) завершил процесс тем же кодом
    return int(app_code)


if __name__ == "__main__":
    # Запуск из командной строки; sys.exit передаёт код возврата оболочке
    sys.exit(main())
