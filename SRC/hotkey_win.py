"""
Модуль hotkey_win.py

Назначение
---------
Обёртка над WinAPI `RegisterHotKey` и фильтр Qt для приёма сообщения `WM_HOTKEY`.
Позволяет регистрировать глобальные сочетания клавиш и реагировать на них в
Qt‑приложении через `QAbstractNativeEventFilter`.

Состав
------
- Константы `WM_HOTKEY` и флаги модификаторов `MOD_*`.
- Функции `register_hotkey` и `unregister_hotkey` для регистрации/снятия горячих клавиш.
- Вспомогательные функции `LO_WORD`/`HI_WORD` для разборки `lParam`.
- Класс `HotkeyFilter`, который перехватывает `WM_HOTKEY` и вызывает ваш handler.

Примечания
---------
- Регистрация с `RegisterHotKey(None, ...)` привязывается к *потоку* GUI.
- Сообщение `WM_HOTKEY` имеет код 0x0312 и приходит в очередь сообщений процесса.
- В `lParam` младшее слово (LO_WORD) — это VK‑код, старшее (HI_WORD) — модификаторы.
"""

from __future__ import annotations
from typing import Any

import ctypes
from ctypes import wintypes

from PyQt6 import QtCore

from SRC.constants import C

# ------------------------------
# Константы WinAPI
# ------------------------------
WM_HOTKEY = 0x0312  # Тип оконного сообщения при срабатывании горячей клавиши
MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_WIN, MOD_NOREPEAT = 0x1, 0x2, 0x4, 0x8, 0x4000

# Доступ к функциям Windows-библиотеки user32.dll
user32 = ctypes.windll.user32


def register_hotkey(hk_id: int, mods: int, vk: int) -> None:
    """Регистрирует глобальную горячую клавишу через WinAPI.

    Параметры
    ---------
    hk_id : int
        Придуманный нами идентификатор горячей клавиши. Возвращается в `wParam` сообщения.
    mods : int
        Маска модификаторов. Комбинируйте `MOD_ALT|MOD_CONTROL|MOD_SHIFT|MOD_WIN`
        и при необходимости `MOD_NOREPEAT`.
    vk : int
        Код основной клавиши (VK_*). См. документацию Microsoft по Virtual-Key Codes.

    Исключения
    ----------
    OSError
        Бросается, если `RegisterHotKey` вернул 0 (ошибка регистрации).
    """
    if not user32.RegisterHotKey(None, hk_id, mods, vk):
        raise OSError(
            C.TEXT_ERROR_REGISTER_HOTKEY.format(hk_id=hk_id, mods=mods, vk=vk)
        )


def unregister_hotkey(hk_id: int) -> None:
    """Снимает ранее зарегистрированную горячую клавишу."""
    user32.UnregisterHotKey(None, hk_id)


def LO_WORD(dword: int) -> int:
    """Возвращает младшее 16-битное слово из 32-битного значения."""
    return dword & 0xFFFF


def HI_WORD(dword: int) -> int:
    """Возвращает старшее 16-битное слово из 32-битного значения."""
    return (dword >> 16) & 0xFFFF


class HotkeyFilter(QtCore.QAbstractNativeEventFilter):
    """Фильтр Qt, вызывающий обработчик при получении `WM_HOTKEY`.

    Обработчик должен иметь сигнатуру `handler(hk_id: int, vk: int, mods: int)` —
    именно в таком порядке параметры формируются в этом модуле.
    """

    def __init__(self, handler):
        """Сохраняет ссылку на пользовательский обработчик горячих клавиш."""
        super().__init__()
        self.handler = handler

    def nativeEventFilter(self, eventType: Any, message: int) -> tuple[bool, int]:
        """Перехватывает нативные события и отбирает только `WM_HOTKEY`.

        Параметры
        ---------
        eventType : Any
            Тип нативного события (на Windows — строка вида "windows_*", не используется)
        message : int
            Указатель на структуру `MSG` WinAPI, приводится через `from_address`

        Возврат
        -------
        tuple[bool, int]
            `(True, 0)`, если событие не должно идти дальше, иначе `(False, 0)`.
        """
        msg = wintypes.MSG.from_address(int(message))
        if msg.message != WM_HOTKEY:
            return False, 0
        hk_id = msg.wParam
        vk = LO_WORD(msg.lParam)
        mods = HI_WORD(msg.lParam)
        try:
            self.handler(hk_id, vk, mods)
        except Exception:
            # Гасим исключения обработчика, чтобы не ломать цикл Qt
            pass
        return True, 0
