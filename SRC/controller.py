"""
Модуль controller.py

Назначение:
    Класс Controller связывает интерфейс пользователя (UI) с обработкой
    глобальных горячих клавиш и специальных клавиш (CapsLock, ScrollLock).

Содержимое:
    - Импорт функций WinAPI для проверки состояния клавиш.
    - Константы кодов левого и правого Control.
    - Класс Controller с методами для обработки событий.
"""

import logging

logger = logging.getLogger(__name__)

from SRC.hotkey_win import (
    register_hotkey,
    unregister_hotkey,
    MOD_CONTROL,  # Требует нажатия клавиши Ctrl
    MOD_NOREPEAT,  # Отключает автоповтор события, если пользователь держит клавишу
)
import SRC.ll_keyboard as llk
from SRC.constants import C


# ID горячих клавиш и идентификатор горячей клавиши
VK_3: int = 0x33  # Код клавиши '3'
VK_4: int = 0x34  # Код клавиши '4'
VK_5: int = 0x35  # Код клавиши '5'
VK_9: int = 0x39  # Код клавиши '9'
VK_CONTROL: int = 0x11  # Модификатор 'ctrl'

HK_MAIN: int = 1  # Логический идентификатор горячей клавиши


class Controller:
    """Контроллер, обрабатывающий события горячих и специальных клавиш."""

    def __init__(self, ui=None):
        """
        Параметры
        ---------
        ui : объект виджета
            Ссылка на UI, в который будут выводиться сообщения.
        """
        self.ui = ui
        self._low_level_hook: llk.KeyboardHook | None = None

    def on_hotkey(self, hk_id: int, mods: int, vk: int):
        """
        Обработчик глобальной горячей клавиши WM_HOTKEY.

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

    def on_caps(self):
        """Вызывается при нажатии CapsLock."""
        try:
            llk.change_keyboard_case()
        except Exception as e:
            logger.error(C.TEXT_ERROR_CHANGE_KEYBOARD.format(e=e))

        return True

    def on_scroll(self):
        """Вызывается при нажатии ScrollLock."""
        self.ui.start_dialogue()

    def register_global_hotkeys(self) -> None:
        """Регистрирует глобальные горячие клавиши и фильтр нативных событий."""
        register_hotkey(HK_MAIN, MOD_CONTROL | MOD_NOREPEAT, VK_3)
        register_hotkey(HK_MAIN, MOD_CONTROL | MOD_NOREPEAT, VK_4)
        register_hotkey(HK_MAIN, MOD_CONTROL | MOD_NOREPEAT, VK_5)
        register_hotkey(HK_MAIN, MOD_CONTROL | MOD_NOREPEAT, VK_9)

    def set_single_hotkeys(self) -> None:
        """Устанавливает низкоуровневый перехватчик CapsLock/ScrollLock."""

        hook = llk.KeyboardHook(
            {
                llk.VK_CAPITAL: self.on_caps,
                llk.VK_SCROLL: self.on_scroll,
            }
        )
        hook.install()
        self._low_level_hook = hook

    def press_ctrl(self, vk: int) -> None:
        llk.press_ctrl(vk)

    def cleanup(self) -> None:
        """Освобождает ресурсы перед завершением приложения"""
        try:
            unregister_hotkey(HK_MAIN)
        except Exception as e:
            logger.warning(C.TEXT_ERROR_UNREGISTER_HOTKEY.format(e=e))
            hook = self._low_level_hook
            if hook is not None:
                try:
                    hook.uninstall()
                except Exception as e:
                    logger.error(C.TEXT_ERROR_UNLOAD_HOOK.format(e=e))
