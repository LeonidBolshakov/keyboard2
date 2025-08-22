# WinAPI RegisterHotKey + перехват WM_HOTKEY
import ctypes
from ctypes import wintypes

from PyQt6 import QtCore

from constants import C

# константы
WM_HOTKEY = 0x0312
MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_WIN, MOD_NOREPEAT = 0x1, 0x2, 0x4, 0x8, 0x4000

user32 = ctypes.windll.user32  # доступ к функциям Windows-библиотеки user32.dll


def register_hotkey(hk_id: int, mods: int, vk: int) -> None:
    """

    Регистрация одной горячей клавиши

    :param hk_id:Внутри программный идентификатор клавиши.
    :param mods: Набор битовых флагов для модификаторов клавиатуры (см. MOD_...).
    :param vk: Код основной клавиши (например, 0x41 для A, 0x70 для F1). Описаны:
                https://learn.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes

    :return: None
    """
    if not user32.RegisterHotKey(None, hk_id, mods, vk):
        raise OSError(C.REG_ERROR.format(hk_id=hk_id, mods=mods, vk=vk))


def unregister_hotkey(hkid: int) -> None:
    user32.UnregisterHotKey(None, hkid)


def LOWORD(dword: int) -> int:
    return dword & 0xFFFF


def HIWORD(dword: int) -> int:
    return (dword >> 16) & 0xFFFF


class HotkeyFilter(QtCore.QAbstractNativeEventFilter):
    """Фильтр Qt. Вызывает handler(hkid, vk, mods) при WM_HOTKEY."""

    def __init__(self, handler):
        super().__init__()
        self.handler = handler

    def nativeEventFilter(self, eventType, message):
        if eventType not in ("windows_generic_MSG", "windows_dispatcher_MSG"):
            return False, 0
        msg = wintypes.MSG.from_address(int(message))
        if msg.message != WM_HOTKEY:
            return False, 0
        hkid = msg.wParam
        vk = LOWORD(msg.lParam)
        mods = HIWORD(msg.lParam)
        try:
            self.handler(hkid, vk, mods)
        except Exception:
            pass
        return True, 0
