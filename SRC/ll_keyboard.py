# -*- coding: utf-8 -*-
"""Утилита для работы с низкоуровневым хуком клавиатуры в Windows.

Класс LowLevelKeyboardHook позволяет регистрировать обработчики для конкретных
виртуальных кодов клавиш (VK). Обработчики вызываются на событие WM_KEYDOWN.

Файл импортируется и на не-Windows платформах: структура и типы объявлены так,
чтобы можно было тестировать логику диспетчеризации без Windows. Установка
хука доступна только в Windows.
"""

from __future__ import annotations

from typing import Callable, Dict, Optional
import time
from dataclasses import dataclass
import ctypes
from ctypes import wintypes
import sys


@dataclass
class Keys:
    KEY_3 = 0x33
    KEY_4 = 0x34
    KEY_5 = 0x35
    KEY_9 = 0x39
    VK_CAPITAL = 0x14
    VK_SCROLL = 0x91
    VK_SHIFT = 0x10
    VK_CONTROL = 0x11
    VK_ALT = 0x12
    VK_RETURN = 0x0D


# ------------------------ Константы Windows ------------------------
WH_KEYBOARD_LL = 13
HC_ACTION = 0

WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105

_KEY_DOWN = {WM_KEYDOWN, WM_SYSKEYDOWN}
_KEY_UP = {WM_KEYUP, WM_SYSKEYUP}
_KEY = _KEY_DOWN | _KEY_UP

# Флаги структуры KBDLLHOOKSTRUCT.flags
LLKHF_EXTENDED = 0x01
LLKHF_LOWER_IL_INJECTED = 0x02
LLKHF_INJECTED = 0x10
LLKHF_ALTDOWN = 0x20
LLKHF_UP = 0x80

# ------------------------ Fallback-типы ----------------------------
# Некоторые IDE-стабы (wintypes.pyi) не объявляют ULONG_PTR/HHOOK.
# Делаем безопасные подстановки по размеру указателя.
try:
    ULONG_PTR = wintypes.ULONG_PTR  # type: ignore[attr-defined]
except AttributeError:
    ULONG_PTR = (
        ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong
    )  # noqa: N816

HHOOK = getattr(wintypes, "HHOOK", wintypes.HANDLE)

# LRESULT может отсутствовать в wintypes.pyi IDE-ставах
try:
    LRESULT = wintypes.LRESULT  # type: ignore[attr-defined]
except AttributeError:
    # LONG_PTR по размеру указателя
    LRESULT = (
        ctypes.c_longlong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_long
    )  # noqa: N816


# ------------------------ Структуры WinAPI -------------------------
# Определение C-структуры, используемой WinAPI.ctypes.wintypes доступен
# на всех платформах, поэтому структуру можно объявить даже на не-Windows.
# ВАЖНО: на x64 обязательно использовать ULONG_PTR для dwExtraInfo (или эквивалент).
class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


# Правильная сигнатура колбэка: LRESULT, WPARAM, LPARAM
LowLevelKeyboardProc = ctypes.WINFUNCTYPE(
    LRESULT,
    ctypes.c_int,  # nCode
    wintypes.WPARAM,  # wParam
    wintypes.LPARAM,  # lParam (указатель на KBDLLHOOKSTRUCT)
)

# Флаг для события клавиатуры:
KEY_EVENT_F_KEYUP = 0x0002  # означает "отпускание клавиши"

# Виртуальные коды клавиш
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_ALT = 0x12
VK_CAPITAL = 0x14
VK_SCROLL = 0x91  # коды CapsLock и ScrollLock

user32 = ctypes.WinDLL("user32", use_last_error=True)  # Функции работы с окнами/вводом
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)  # Общесистемные функции


class LowLevelKeyboardHook:
    """Диспетчер низкоуровневых событий клавиатуры для зарегистрированных обработчиков

    handlers: dict[int, Callable[[], None]]
        Ключ — виртуальный код клавиши (VK_*), значение — функция без аргументов.
    """

    def __init__(self, handlers: Dict[int, Callable[[], None]]):
        self.handlers = handlers
        self._hook_id: Optional[int] = None
        self._callback = None
        self._pressed: set[int] = set()

        if sys.platform.startswith("win"):
            # Инициализируем WinAPI.
            # Создаём C-совместимый колбэк
            self._callback = LowLevelKeyboardProc(self._low_level_callback)

            # Прототипы функций
            user32.SetWindowsHookExW.argtypes = [
                ctypes.c_int,  # idHook
                LowLevelKeyboardProc,  # lpfn
                wintypes.HINSTANCE,  # hMod
                wintypes.DWORD,  # dwThreadId
            ]
            user32.SetWindowsHookExW.restype = HHOOK

            user32.CallNextHookEx.argtypes = [
                HHOOK,
                ctypes.c_int,
                wintypes.WPARAM,
                wintypes.LPARAM,
            ]
            user32.CallNextHookEx.restype = LRESULT

            user32.UnhookWindowsHookEx.argtypes = [HHOOK]
            user32.UnhookWindowsHookEx.restype = wintypes.BOOL
        else:
            raise OSError("Программа работает только под управлением Windows")

    # ------------------------------------------------------------------
    def install(self) -> None:
        """Установить низкоуровневый хук клавиатуры.

        Для WH_KEYBOARD_LL загружать DLL не нужно: hMod=0, dwThreadId=0.
        """
        if not sys.platform.startswith("win"):
            raise RuntimeError("LowLevelKeyboardHook доступен только в Windows")

        self._hook_id = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._callback, 0, 0)
        if not self._hook_id:
            raise ctypes.WinError()

    # ------------------------------------------------------------------
    def uninstall(self) -> None:
        """Снять установленный хук."""
        if self._hook_id:
            user32.UnhookWindowsHookEx(self._hook_id)
            self._hook_id = None

    # ------------------------------------------------------------------
    def _low_level_callback(self, nCode: int, wParam: int, lParam: int) -> int:
        """Внутренний колбэк хука.

        При WM_KEYDOWN получает vkCode и, если он есть в handlers, вызывает обработчик.
        Передаёт событие дальше по цепочке через CallNextHookEx если вызванный обработчик вернул False
        """
        if nCode != HC_ACTION:
            return user32.CallNextHookEx(self._hook_id, nCode, wParam, lParam)

        if wParam not in _KEY:
            return user32.CallNextHookEx(self._hook_id, nCode, wParam, lParam)

        kb = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
        is_keyup = (wParam in _KEY_UP) or bool(kb.flags & LLKHF_UP)

        if is_keyup:
            # только освобождаем состояние, обработчик НЕ вызываем
            self._pressed.discard(kb.vkCode)
            return user32.CallNextHookEx(self._hook_id, nCode, wParam, lParam)

        # keydown: фиксируем и вызываем обработчик
        self._pressed.add(kb.vkCode)
        handler = self.handlers.get(kb.vkCode)

        block = False
        if handler:
            try:
                block = bool(handler())  # старая сигнатура без аргументов
            except Exception:
                block = False

        if block:
            return 1
        return user32.CallNextHookEx(self._hook_id, nCode, wParam, lParam)


def press_ctrl_and(key_code: int, delay: float = 0.05):
    """
    Эмулирует комбинацию Ctrl+<Key> через WinAPI (keybd_event).

    Параметры:
        key_code : int
            Виртуальный код клавиши (например 0x43 для 'C', 0x56 для 'V').
        delay : float
            Задержка между событиями клавиш в секундах (по умолчанию 0.05).

    Логика:
        1. Нажать Ctrl (keydown).
        2. Нажать указанную клавишу (keydown).
        3. Отпустить указанную клавишу (keyup).
        4. Отпустить Ctrl (keyup).
    """

    # 1. Ctrl down
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    time.sleep(delay)

    # 2. Key down
    user32.keybd_event(key_code, 0, 0, 0)
    time.sleep(delay)

    # 3. Key up
    user32.keybd_event(key_code, 0, KEY_EVENT_F_KEYUP, 0)
    time.sleep(delay)

    # 4. Ctrl up
    user32.keybd_event(VK_CONTROL, 0, KEY_EVENT_F_KEYUP, 0)


__all__ = [
    "LowLevelKeyboardHook",
    "KBDLLHOOKSTRUCT",
    "WM_KEYDOWN",
    "WH_KEYBOARD_LL",
    "LLKHF_UP",
]
