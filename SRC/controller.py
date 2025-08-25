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

# Коды виртуальных клавиш: левый и правый Ctrl

from SRC import ll_keyboard

def safe_slot(fn):
    def _w(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            print(f'Ошибка в слоте {fn.__name__}:', e)
    return _w


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

    @safe_slot


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

    @safe_slot


    def on_caps(self):
        """Вызывается при нажатии CapsLock."""
        ll_keyboard.change_keyboard_case()

        return True

    @safe_slot


    def on_scroll(self):
        """Вызывается при нажатии ScrollLock."""
        self.ui.start_dialogue()