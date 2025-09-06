"""
Модуль windows_hotkeys.py

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

import ctypes
from ctypes import wintypes
from typing import Iterable, cast
from PyQt6.QtCore import QObject, QByteArray

from PyQt6 import QtCore
from PyQt6.sip import voidptr

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

    def __init__(self) -> None:
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
        """
        Регистрирует набор глобальных горячих клавиш.

        :param keys: Множество виртуальных кодов клавиш (VK_*).
        :param mods: Модификаторы (строка с пробелами или итерируемая коллекция).
        """
        mods_list = self._prepare_mods(mods)
        mask = self.mods_to_mask(mods_list)
        for reg_id, vk in enumerate(keys, start=1):
            self._register_hotkey(reg_id, mask, vk)
            self._reg_ids.append(reg_id)

    def _register_hotkey(self, reg_id: int, mask: int, vk: int) -> None:
        """
        Вызывает WinAPI RegisterHotKey для одной клавиши.
        :param reg_id: Идентификатор регистрации
        :param mask: битовая маска модификаторов
        :param vk: виртуальный код клавиши
        :raises OSError: если регистрация не удалась
        """
        ok = user32.RegisterHotKey(None, reg_id, mask, vk)
        if not ok:
            raise OSError(ctypes.WinError(ctypes.get_last_error()))

    def _prepare_mods(self, mods: Iterable[str] | str) -> list[str]:
        """
        Преобразует входные модификаторы в список:
        - разбивает строку на слова (если передана строка)
        - удаляет пустые элементы
        - добавляет "norepeat"
        - удаляет дубликаты, сохраняя порядок
        """
        items = mods.split() if isinstance(mods, str) else list(mods)
        items = [m.lower().strip() for m in items if m.strip()]
        items.append("norepeat")
        return self._unique_preserve_order(items)

    def _unique_preserve_order(self, items: Iterable[str]) -> list[str]:
        """
        Возвращает новый список без дубликатов,
        сохраняя исходный порядок элементов.
        """
        already_is: set[str] = set()
        out: list[str] = []
        for m in items:
            if m not in already_is:
                already_is.add(m)
                out.append(m)
        return out

    def cleanup(self) -> None:
        """Освобождает ресурсы перед завершением приложения"""
        for hk_id in self._reg_ids:
            ok = user32.UnregisterHotKey(None, hk_id)
            if not ok:
                raise ctypes.WinError(ctypes.get_last_error())

        self._reg_ids.clear()

    def mods_to_mask(self, mods_str: Iterable[str]) -> int:
        """
        Собирает модификаторы в маску
        :param mods_str: Iterable[str] - список модификаторов
        :return: int - маска
        """
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

    def nativeEventFilter(
        self,
        eventType: (
            QByteArray | bytes | bytearray | memoryview
        ),  # расширенный тип, как у базового,
        message: voidptr | None,
    ) -> tuple[bool, voidptr | None]:
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
            `(True, voidptr(0))`, если событие не должно идти дальше, иначе `(False, voidptr(0))`.
        """
        if message is None:
            return False, voidptr(0)

        msg = wintypes.MSG.from_address(int(message))  # type: ignore[arg-type]
        if msg.message != self.WM_HOTKEY:
            return False, voidptr(0)

        hk_id = msg.wParam
        vk = HI_WORD(msg.lParam)  # VK
        mods = LO_WORD(msg.lParam)  # MOD_*
        try:
            self.handler(hk_id, vk, mods)
        except Exception:
            # Гасим исключения обработчика, чтобы не ломать цикл Qt
            pass
        return True, voidptr(0)
