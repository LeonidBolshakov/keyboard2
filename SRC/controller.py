"""
Модуль controller.py

Назначение:
    Класс Controller связывает интерфейс пользователя (UI) с обработкой
    глобальных горячих клавиш и специальных клавиш (CapsLock, ScrollLock).
"""

from typing import Callable
import logging

logger = logging.getLogger(__name__)

from SRC.windows_hotkeys import HotkeysWin
from SRC.hotkeys_handlers import HotkeysHandlers as HotkeysHandlers
from SRC.try_log import log_exceptions
from SRC.input_keys import SendInputKeyboard
import SRC.ll_keyboard as llk
from SRC.constants import C


class Controller:
    """Контроллер, обрабатывающий события горячих и специальных клавиш."""

    def __init__(self) -> None:
        """
        Параметры
        ---------
        ui : объект виджета
            Ссылка на UI, в который будут выводиться сообщения.
        """
        self.llk_hook: llk.LowLevelKeyboardHook | None = None
        self.hw = HotkeysWin()
        self.hotkeys_handlers = HotkeysHandlers()
        self.send_input_keyboards = SendInputKeyboard()
        self.keys = llk.Keys()

    @log_exceptions
    def register_global_hotkeys(self):
        hotkeys_win_ctrl = {
            self.keys.KEY_3,
            self.keys.KEY_4,
            self.keys.KEY_5,
            self.keys.KEY_9,
        }
        self.hw.register_global_hotkeys(hotkeys_win_ctrl, "control")

    @log_exceptions
    def set_single_hotkeys(self) -> None:
        llk.reset_caps_lock()  # выключаем CapsLock
        hotkeys_llk: dict[int, Callable] = {
            self.keys.VK_CAPITAL: self.hotkeys_handlers.on_caps,
            self.keys.VK_SCROLL: self.hotkeys_handlers.on_scroll,
        }
        self.llk_hook = llk.LowLevelKeyboardHook(hotkeys_llk)
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
        match vk:
            case self.keys.KEY_3:
                self.hotkeys_handlers.send_mail()
            case self.keys.KEY_4:
                self.hotkeys_handlers.send_telephone()
            case self.keys.KEY_5:
                self.hotkeys_handlers.run_calculator()
            case self.keys.KEY_9:
                self.hotkeys_handlers.send_signature()

    def press_ctrl_and(self, vk: int, delay_sec: float = C.TIME_DELAY_CTRL_C_V) -> None:
        self.send_input_keyboards.press_ctrl_and_vk(vk, delay_sec)
        # llk.press_ctrl_and(vk, delay_sec)

    def cleanup(self):
        self.hw.cleanup()
