import subprocess
import logging

from SRC.try_log import log_exceptions
from SRC.signals import signals_bus
from SRC.get_variable import Variables
from SRC.ll_keyboard import Keys
from SRC.lib_keyboard import LibKeyboard
from SRC.constants import C

logger = logging.getLogger(__name__)


class HotkeysHandlers:
    """Обработчики глобальных горячих клавиш.

    Методы вызываются из модуля низкоуровневой клавиатуры при срабатывании
    соответствующих комбинаций. Основные действия: смена раскладки, запуск
    программ, вставка заранее заданных переменных в активное окно.
    """

    def __init__(self) -> None:
        """Инициализирует доступ к хранилищу переменных."""
        self.vars = Variables()
        self.lib_kbd = LibKeyboard()  # types ignore
        self.keys = Keys()

    def write_var(self, name: str) -> None:
        """Если переменная существует, вставляет её содержимое в активное окно."""
        if value := self.vars.get_var(name):
            self.lib_kbd.write_text(value)

    @log_exceptions(C.TEXT_ERROR_CHANGE_KEYBOARD)
    def on_caps(self) -> bool:
        """Обработка нажатия CapsLock.

        :return: True – подавить дальнейшую обработку.
        """
        self.change_register()
        return True

    @staticmethod
    def on_scroll() -> bool:
        """Обработка нажатия ScrollLock.

        :return: True – подавить дальнейшую обработку.
        """
        signals_bus.start_dialog.emit()
        return True

    @log_exceptions(C.TEXT_ERROR_SEND_EMAIL)
    def send_mail(self) -> None:
        """Вставляет адрес e-mail в текущее активное окно, если переменная определена."""
        self.write_var("e-mail")

    @log_exceptions(C.TEXT_ERROR_SEND_TELEPHONE)
    def send_telephone(self) -> None:
        """Вставляет телефон в активное окно, если переменная определена."""
        self.write_var("telephone")

    def run_calculator(self) -> None:
        """Запускает внешний калькулятор по пути из переменной calculator."""
        if calculator := self.vars.get_var("calculator"):
            try:
                subprocess.Popen([calculator])
            except OSError as e:
                logger.warning(
                    C.TEXT_ERROR_RUN_CALCULATOR.format(calculator=calculator, e=e)
                )

    @log_exceptions(C.TEXT_ERROR_SEND_SIGNATURE)
    def send_signature(self) -> None:
        """Вставляет две строки подписи."""
        self.write_var("signature")

    def change_register(self) -> None:
        self.lib_kbd.send_key("alt+shift")
