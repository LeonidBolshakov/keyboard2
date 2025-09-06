import time, threading
import logging

logger = logging.getLogger(__name__)

from keyboard import send, release, write

from SRC.constants import _Const as C


class LibKeyboard:
    def write_text(self, text: str) -> None:
        """
        Эмулирует набор текста с помощью библиотеки `keyboard`.

        Аргументы:
            text: Строка для вывода. Подстрока ``"\\n"`` заменяется на перевод строки.

        Поведение:
            - Перед выводом пытается отпустить модификаторы (Ctrl, Alt, Shift, Win),
              чтобы текст набирался в «чистом» состоянии.
            - Добавляет короткую паузу (30 мс), затем быстро выводит весь текст
              (`delay=0`, без восстановления состояния клавиш).
            - Вся операция выполняется в отдельном потоке через `threading. Timer(0.05, go)` —
              это не блокирует основной поток.

        Обработка ошибок:
            - `OSError`, `PermissionError` — логируются сообщением о невозможности
              синтетического ввода (обычно нет прав или ввод заблокирован системой).
            - Любые другие исключения так же логируются.
        """

        def go():
            try:
                for m in ("ctrl", "alt", "shift", "windows"):
                    try:
                        release(m)
                    except:
                        pass
                time.sleep(0.03)

                lines = text.split(r"\n")
                for i, line in enumerate(lines):
                    write(line, delay=0, restore_state_after=False, exact=True)
                    if i < len(lines) - 1:
                        send("shift+enter")
            except (OSError, PermissionError) as e:
                # записываем в журнал отказ системы от синтетического ввода
                logger.error(C.LOGGER_TEXT_ERROR_KEYBOARD.format(e=e))
            except Exception as e:
                logger.exception(C.LOGGER_TEXT_UNCAUGHT.format(e=e))

        threading.Timer(0.05, go).start()

    def send_key(self, key: str) -> None:
        """
        Отправляет одиночное нажатие клавиши.

        Аргументы:
            key: Имя клавиши, совместимое с библиотекой `keyboard` (например, ``"enter"``).

        Поведение:
            Вызывает `keyboard.send(key)` для эмуляции нажатия.

        Обработка ошибок:
            - `OSError`, `PermissionError` — логируются сообщением о невозможности
              синтетического ввода.
            - Любые другие исключения так же логируются.
        """
        try:
            send(key)
        except (OSError, PermissionError) as e:
            # записываем в журнал отказ синтетического ввода
            logger.error(C.LOGGER_TEXT_ERROR_KEYBOARD.format(e=e))
        except Exception as e:
            logger.exception(C.LOGGER_TEXT_UNCAUGHT.format(e=e))
