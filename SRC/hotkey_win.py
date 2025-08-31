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
- В `lParam` младшее слово (LO_WORD) — это модификаторы, старшее (HI_WORD) — VK-код
"""

from __future__ import annotations
from typing import Any

import ctypes
from ctypes import wintypes

from PyQt6 import QtCore
from PyQt6.QtCore import QObject
from collections.abc import Iterable

# Доступ к функциям Windows-библиотеки user32.dll
user32 = ctypes.windll.user32


def LO_WORD(dword: int) -> int:
    """Возвращает младшее 16-битное слово из 32-битного значения."""
    return dword & 0xFFFF


def HI_WORD(dword: int) -> int:
    """Возвращает старшее 16-битное слово из 32-битного значения."""
    return (dword >> 16) & 0xFFFF


class HotkeysWin(QObject):
    # ------------------------------
    # Константы WinAPI
    # ------------------------------

    MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_WIN, MOD_NOREPEAT = 0x1, 0x2, 0x4, 0x8, 0x4000

    def __init__(self):
        super().__init__()

        self.keys: set[int] = set()
        self._reg_ids: list[int] = []
        self.str_to_mod: dict[str, int] = {
            "alt": self.MOD_ALT,
            "control": self.MOD_CONTROL,
            "shift": self.MOD_SHIFT,
            "win": self.MOD_WIN,
            "norepeat": self.MOD_NOREPEAT,
        }

    def register_global_hotkeys(
        self, keys: set[int], mods: Iterable[str] | str
    ) -> None:
        """Регистрирует глобальные горячие клавиши"""
        if isinstance(mods, str):
            mods = mods.split()

        mods.append("norepeat")
        mask = self.mods_to_mask(mods)

        id_counter = 1
        for key in keys:
            ok = user32.RegisterHotKey(None, id_counter, mask, key)
            if not ok:
                raise OSError(ctypes.WinError(ctypes.get_last_error()))
            self._reg_ids.append(id_counter)
            id_counter += 1

    def cleanup(self) -> None:
        """Освобождает ресурсы перед завершением приложения"""
        for hk_id in self._reg_ids:
            ok = user32.UnregisterHotKey(None, hk_id)
            if not ok:
                raise ctypes.WinError(ctypes.get_last_error())

        self._reg_ids.clear()

    def mods_to_mask(self, mods_str: Iterable[str]) -> int:
        mask = 0
        for mod_str in mods_str:
            mask |= self.str_to_mod[mod_str]

        return mask


class HotkeyFilter(QtCore.QAbstractNativeEventFilter):
    """Фильтр Qt, вызывающий обработчик при получении `WM_HOTKEY`.

    Обработчик должен иметь сигнатуру `handler(hk_id: int, vk: int, mods: int)` —
    именно в таком порядке параметры формируются в этом модуле.
    """

    WM_HOTKEY = 0x0312  # Тип оконного сообщения при срабатывании горячей клавиши

    def __init__(self, handler):
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
        if msg.message != self.WM_HOTKEY:
            return False, 0

        hk_id = msg.wParam
        vk = HI_WORD(msg.lParam)  # VK
        mods = LO_WORD(msg.lParam)  # MOD_*
        try:
            self.handler(hk_id, vk, mods)
        except Exception:
            # Гасим исключения обработчика, чтобы не ломать цикл Qt
            pass
        return True, 0
