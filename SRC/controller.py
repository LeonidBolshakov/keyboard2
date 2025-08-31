"""
Модуль controller.py

Назначение:
    Класс Controller связывает интерфейс пользователя (UI) с обработкой
    глобальных горячих клавиш и специальных клавиш (CapsLock, ScrollLock).
"""

from typing import Callable
import logging

logger = logging.getLogger(__name__)

from SRC.hotkey_win import HotkeysWin
from SRC.try_log import log_exceptions
from SRC.signals import signals_bus
import SRC.ll_keyboard as llk
from SRC.constants import C


class Controller:
    """Контроллер, обрабатывающий события горячих и специальных клавиш."""

    def __init__(self):
        """
        Параметры
        ---------
        ui : объект виджета
            Ссылка на UI, в который будут выводиться сообщения.
        """
        self.llk_hook: llk.KeyboardHook | None = None
        self.hw = HotkeysWin()

    @log_exceptions
    def register_global_hotkeys(self):
        hotkeys_win_ctrl = {ord("3"), ord("4"), ord("5"), ord("9")}
        self.hw.register_global_hotkeys(hotkeys_win_ctrl, "control")

    @log_exceptions
    def set_single_hotkeys(self):
        hotkeys_llk: dict[int:Callable] = {
            llk.VK_CAPITAL: self.on_caps,
            llk.VK_SCROLL: self.on_scroll,
        }
        self.llk_hook = llk.KeyboardHook(hotkeys_llk)
        self.llk_hook.install()

    @log_exceptions
    def on_hotkey(self, hk_id: int, vk: int, mods: int):
        """
        Обработчик нажатий системных горячих клавиш.

        Параметры
        ---------
        hk_id : int
            Идентификатор зарегистрированной горячей клавиши.
        vk : int
            Код виртуальной клавиши.
        mods : int
            Маска модификаторов (Alt, Ctrl, Shift, Win).
        """
        # Добавляем сообщение в UI
        print(f"WM_HOTKEY id={hk_id} vk=0x{vk:X} mods=0x{mods:X}")

    @staticmethod
    @log_exceptions(C.TEXT_ERROR_CHANGE_KEYBOARD)
    def on_caps() -> bool:
        """
        Вызывается при нажатии CapsLock.

        :return: True - Дальнейшую обработку подавить. False - обработку продолжить.
        """
        llk.change_keyboard_case()
        return True

    @staticmethod
    def on_scroll() -> bool:
        """Вызывается при нажатии ScrollLock.

        :return: True - Дальнейшую обработку подавить. False - обработку продолжить.
        """

        signals_bus.start_dialog.emit()
        return True

    def press_ctrl(self, vk: int) -> None:
        llk.press_ctrl(vk)

    def cleanup(self):
        self.hw.cleanup()
