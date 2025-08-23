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

import ctypes

# Импортируем функцию WinAPI для проверки состояния клавиш
GetAsyncKeyState = ctypes.windll.user32.GetAsyncKeyState

# Коды виртуальных клавиш: левый и правый Ctrl
VK_LCONTROL, VK_RCONTROL = 0xA2, 0xA3


class Controller:
    """Контроллер, обрабатывающий события горячих и специальных клавиш."""

    def __init__(self, ui):
        """
        Параметры
        ---------
        ui : объект виджета
            Ссылка на UI, в который будут выводиться сообщения.
        """
        self.ui = ui

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
        # Проверяем отдельно состояние левого и правого Ctrl
        left = bool(GetAsyncKeyState(VK_LCONTROL) & 0x8000)
        right = bool(GetAsyncKeyState(VK_RCONTROL) & 0x8000)

        # Добавляем сообщение в UI
        self.ui.append(
            f"WM_HOTKEY id={hk_id} vk=0x{vk:X} mods=0x{mods:X} L={left} R={right}"
        )

    def on_caps(self):
        """Вызывается при нажатии CapsLock."""
        self.ui.append("CapsLock pressed")

    def on_scroll(self):
        """Вызывается при нажатии ScrollLock."""
        self.ui.append("ScrollLock pressed")
