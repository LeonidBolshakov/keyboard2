"""
Точка входа приложения.

Назначение
---------.
Инициализирует логирование, запускает основное Qt‑приложение и корректно
обрабатывает исключения на верхнем уровне, возвращая код завершения процессу.

Состав модуля
-------------
- Инициирует настройку логирования (`TuneLogger`).
- Инициирует класс приложения (`MainApp`).
- Определяет функцию `main()` как оболочку запуска с обработкой ошибок.
- Вызывает запуск при исполнении файла как скрипта.

Примечание
---------
`MainApp().main_app()` возвращает целочисленный код выхода Qt‑цикла (результат
`QApplication.exec()`), который далее используется как код завершения процесса.
"""

# ---- Точка входа
import sys
import logging as lg

logger = lg.getLogger(__name__)

from SRC.tune_logger import TuneLogger
from SRC.app import StartApp
from SRC.constants import C


def keyboard2() -> int:
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
        # Если логгер не настроился, выводим сообщение и продолжаем запуск
        lg.basicConfig(level=lg.INFO, stream=sys.stderr)
        lg.getLogger().exception(C.TEXT_ERROR_TUNE_LOGGER.format(e=e))

    try:
        return int(StartApp().main_app())
    except SystemExit as e:
        return int(getattr(e, "code", 0) or 0)
    except KeyboardInterrupt:
        return 130
    except Exception as e:
        # Записываем в лог не перехваченное исключение и выходим с кодом 1
        logger.exception(C.TEXT_ERROR_START_APP.format(e=e))
        return 1  # Возвращаем код, чтобы sys.exit(main()) завершил процесс тем же кодом
    finally:
        lg.shutdown()


if __name__ == "__main__":
    # Запуск из командной строки; sys.exit передаёт код возврата оболочке
    sys.exit(keyboard2())
