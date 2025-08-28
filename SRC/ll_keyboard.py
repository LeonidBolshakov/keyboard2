"""
Модуль ll_keyboard.py

Назначение
---------
Низкоуровневый перехватчик клавиатуры для клавиш **CapsLock** и **ScrollLock**.
Эти клавиши нельзя зарегистрировать как системные горячие клавиши - они идут без модификатора.
Реализует установку и снятие перехватчика через функции Windows и вызов
пользовательских обработчиков при нажатии.

Состав
------
- Константы: идентификаторы хука и сообщения клавиатуры.
- Описание структуры, описывающей событие клавиши.
- Обёртки над функциями библиотеки user32: установка/снятие хука и вызов
  следующего в цепочке.
- Класс `KeyboardHook` с методами `install()` и `uninstall()` и внутренним
  обработчиком `_callback`.

Примечания по использованию
---------------------------
- Хук работает в контексте потока графического интерфейса. Вызывайте `install()`
  после создания `QApplication` и храните объект `KeyboardHook`, чтобы его не
  уничтожила сборка мусора.
- Обязательно вызывайте `uninstall()` перед завершением приложения, либо
  подключите его к сигналу `aboutToQuit`.
"""

from __future__ import annotations

import ctypes
import time
from ctypes import wintypes
from typing import Callable

WH_KEYBOARD_LL = 13  # Идентификатор низкоуровневого клавиатурного хука
WM_KEYDOWN, WM_SYS_KEYDOWN = 0x0100, 0x0104  # Идентификатор сообщения о нажатии клавиши
WM_KEYUP = 0x0100, 0x0101
WM_SYS_KEY_DOWN, WM_SYS_KEY_UP = 0x0104, 0x0105

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

# В стандартных типах ctypes.wintypes нет U_LONG_PTR и L_RESULT,
# поэтому определяем их вручную с учётом разрядности.
if ctypes.sizeof(ctypes.c_void_p) == 8:
    U_LONG_PTR = ctypes.c_ulonglong
    L_RESULT = ctypes.c_longlong
else:
    U_LONG_PTR = ctypes.c_ulong
    L_RESULT = ctypes.c_long

HHOOK = ctypes.c_void_p  # Указатель на тип void* из C


class KbdLlHookStruct(ctypes.Structure):
    """Структура Windows API, описывающая событие низкоуровневого хука."""

    _fields_ = [
        ("vkCode", wintypes.DWORD),  # код клавиши
        ("scanCode", wintypes.DWORD),  # скан-код (код сканирования клавиши)
        ("flags", wintypes.DWORD),  # флаги события
        ("time", wintypes.DWORD),  # время события
        ("dwExtraInfo", U_LONG_PTR),  # дополнительная информация
    ]


LowLevelKeyboardProc = ctypes.WINFUNCTYPE(  # создаёт класс-обёртку для обратных вызовов (stdcall),
    # используется для регистрации Python-функции как C-указателя
    L_RESULT,
    ctypes.c_int,
    wintypes.WPARAM,
    wintypes.LPARAM,
)

SetWindowsHookExW = (
    user32.SetWindowsHookExW
)  # установка хука (низкоуровневого обработчика)
SetWindowsHookExW.argtypes = [
    wintypes.INT,  # идентификатор хука
    LowLevelKeyboardProc,  # функция обратного вызова
    wintypes.HINSTANCE,  # дескриптор модуля
    wintypes.DWORD,  # идентификатор потока (0 = глобально)
]
SetWindowsHookExW.restype = HHOOK  # возвращает дескриптор хука

UnhookWindowsHookEx = user32.UnhookWindowsHookEx  # снятие установленного хука
UnhookWindowsHookEx.argtypes = [HHOOK]  # принимает дескриптор хука
UnhookWindowsHookEx.restype = wintypes.BOOL  # возвращает успех/неудачу

CallNextHookEx = user32.CallNextHookEx  # передача события следующему хуку в цепочке
CallNextHookEx.argtypes = [
    HHOOK,  # дескриптор текущего хука (обычно None)
    ctypes.c_int,  # код хука
    wintypes.WPARAM,  # параметр wParam
    wintypes.LPARAM,  # параметр lParam
]
CallNextHookEx.restype = L_RESULT  # возвращает результат обработки


class KeyboardHook:
    """
    Класс-обёртка для регистрации низкоуровневого перехватчика клавиатуры.

    Пользователь создаёт объект и вызывает install(), после чего Windows
    сама вызывает _callback на каждое клавиатурное событие. Внутри _callback
    по коду клавиши сама запускает соответствующий пользовательский обработчик.

    Параметры конструктора
    ----------------------
    handlers : dict[int, Callable[[], None]]
        Сопоставление {VK-код: обработчик}.
        Пример: {VK_CAPITAL: on_caps, VK_SCROLL: on_scroll}.

    Замечание: объект нужно хранить в переменной/атрибуте, иначе сборщик мусора
    уничтожит его и хук перестанет работать.
    """

    def __init__(self, handlers: dict[int, Callable[[], None]]):
        self.handlers = handlers
        self.hook: HHOOK | None = None
        self._proc = LowLevelKeyboardProc(self._callback)
        # self._proc - объект, который:

        # хранит ссылку на метод _callback,
        # имеет «C-совместимую» сигнатуру (L_RESULT CALLBACK(int, WPARAM, LPARAM)),
        # может быть передан в WinAPI как указатель на функцию.
        #
        # То есть self._proc = «C-указатель на Python-функцию»

    def install(self) -> None:
        """Устанавливает низкоуровневый хук"""
        self.hook = SetWindowsHookExW(WH_KEYBOARD_LL, self._proc, 0, 0)
        if not self.hook:
            err = ctypes.get_last_error()
            buf = ctypes.create_unicode_buffer(512)
            kernel32.FormatMessageW(0x00001000, None, err, 0, buf, len(buf), None)
            raise OSError(f"Ошибка установки хука: код={err}: {buf.value.strip()}")

    def uninstall(self) -> None:
        """Снимает установленный хук, если он есть."""
        if self.hook:
            UnhookWindowsHookEx(self.hook)
            self.hook = None

    def _callback(
        self, nCode: int, wParam: wintypes.WPARAM, lParam: wintypes.LPARAM
    ) -> L_RESULT:
        """Внутренний обратный вызов. Запускает обработчик по vkCode, если он задан."""
        if nCode == 0 and wParam in (
            WM_KEYDOWN,
            WM_KEYUP,
            WM_SYS_KEY_DOWN,
            WM_SYS_KEY_UP,
        ):
            ks = ctypes.cast(lParam, ctypes.POINTER(KbdLlHookStruct)).contents
            handler = self.handlers.get(ks.vkCode)
            if handler is not None:
                handler()  # вызываем свой код
                return 1  # полностью съедаем событие (и down, и up)
        return CallNextHookEx(None, nCode, wParam, lParam)


def press_ctrl(key_code: int, delay: float = 0.05):
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


def change_keyboard_case() -> None:
    """
    Эмулирует комбинацию Ctrl+Shift через WinAPI (keybd_event).


    Логика:
        1. Нажать Alt (keydown).
        2. Нажать Shift (keydown).
        3. Отпустить Shift (keyup).
        4. Отпустить Alt (keyup).
    """
    user32.keybd_event(VK_ALT, 0, 0, 0)  # 1. Alt down
    user32.keybd_event(VK_SHIFT, 0, 0, 0)  # 2. Shift down
    user32.keybd_event(VK_SHIFT, 0, KEY_EVENT_F_KEYUP, 0)  # 3. Shift up
    user32.keybd_event(VK_ALT, 0, KEY_EVENT_F_KEYUP, 0)  # 4. Alt up


# ----- базовые типы -----
U_LONG_PTR = ctypes.c_uint64 if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_uint32

# ----- константы -----
INPUT_KEYBOARD = 1
KEY_EVENT_F_KEYUP = 0x0002
KEY_EVENT_F_UNICODE = 0x0004

VK_SHIFT, VK_CONTROL, VK_MENU = 0x10, 0x11, 0x12


# ----- структуры -----
class KeyboardInput(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", U_LONG_PTR),
    ]


class _InputUnion(ctypes.Union):
    _fields_ = [("ki", KeyboardInput)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _InputUnion)]


def make_key(vk, up=False):
    return INPUT(
        type=INPUT_KEYBOARD,
        u=_InputUnion(
            ki=KeyboardInput(
                wVk=vk,
                wScan=0,
                dwFlags=(KEY_EVENT_F_KEYUP if up else 0),
                time=0,
                dwExtraInfo=0,
            )
        ),
    )


def send_text(text: str):
    seq = []
    for ch in text:
        code = user32.VkKeyScanW(ord(ch))
        vk = code & 0xFF

        # символ
        seq.append(make_key(vk, False))
        seq.append(make_key(vk, True))

    arr = (INPUT * len(seq))(*seq)
    user32.SendInput(len(arr), ctypes.byref(arr), ctypes.sizeof(INPUT))
