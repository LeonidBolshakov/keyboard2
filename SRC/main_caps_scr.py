"""
Windows-only:
- глобальный хоткей Ctrl+H через RegisterHotKey + WM.HOTKEY в Qt-цикле
- перехват одиночных клавиш CapsLock и ScrollLock через WH_KEYBOARD_LL

requirements:
    PyQt6
"""

import sys
import ctypes
import logging
from ctypes import wintypes
from PyQt6 import QtCore, QtWidgets
from typing import Final
from enum import IntEnum


# --- Windows Messages (WM) — перечисление основных кодов оконных сообщений
class WM(IntEnum):
    HOTKEY = 0x0312  # глобальный хоткей (сообщение приходит после RegisterHotKey)
    KEYDOWN = 0x0100  # нажатие клавиши (для окон с фокусом)
    KEYUP = 0x0101  # отпускание клавиши (для окон с фокусом)
    SYSKEYDOWN = 0x0104  # системное нажатие (Alt и пр.)
    SYSKEYUP = 0x0105  # системное отпускание


# --- MOD — флаги-модификаторы для RegisterHotKey
class MOD(IntEnum):
    ALT = 0x0001
    CONTROL = 0x0002
    SHIFT = 0x0004
    WIN = 0x0008
    NOREPEAT = 0x4000  # Vista+: блокирует автоповтор при удержании сочетания


WH_KEYBOARD_LL: Final = 13  # Low-Level Keyboard Hook — глобальный LL-хук клавиатуры


# --- VK — виртуальные коды клавиш
class VK(IntEnum):
    H = 0x48
    LCONTROL = 0xA2
    RCONTROL = 0xA3
    CAPITAL = 0x14  # CapsLock
    SCROLL = 0x91  # ScrollLock


# --- LLKHF — флаги из поля KBDLLHOOKSTRUCT.flags
class LLKHF(IntEnum):
    EXTENDED = 0x01  # extended-key (обычно правые клавиши блока)
    INJECTED = 0x10  # событие сгенерировано программно
    ALTDOWN = 0x20  # нажат Alt
    UP = 0x80  # отпускание (key up)


MOD_NOREPEAT = 0x4000  # Vista+: явная константа, если не используете Enum

HK_MAIN: Final = 1  # идентификатор нашего глобального хоткея (wParam в WM.HOTKEY)

# ---- user32/kernel32 с учётом last_error (для диагностики WinAPI ошибок)
user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

# ---- pointer-sized типы (совместимость 32/64-бит)
PTR_64 = ctypes.sizeof(ctypes.c_void_p) == 8
ULONG_PTR = getattr(
    wintypes, "ULONG_PTR", ctypes.c_ulonglong if PTR_64 else ctypes.c_ulong
)
LRESULT = getattr(wintypes, "LRESULT", ctypes.c_longlong if PTR_64 else ctypes.c_long)
HHOOK = getattr(wintypes, "HHOOK", ctypes.c_void_p)  # дескриптор хука (указатель)


# ---- KBDLLHOOKSTRUCT — KeyBoard Low-Level Hook STRUCTure
# Структура, которую система передаёт в колбэк low-level-хука клавиатуры (WH_KEYBOARD_LL).
# Содержит подробности события клавиши.
class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),  # виртуальный код клавиши (VK_*)
        ("scanCode", wintypes.DWORD),  # аппаратный scancode клавиши
        ("flags", wintypes.DWORD),  # флаги LLKHF_* (extended/injected/alt/up)
        ("time", wintypes.DWORD),  # время события (мс от старта системы)
        ("dwExtraInfo", ULONG_PTR),  # дополнительные данные (например, от SendInput)
    ]


# ---- LowLevelKeyboardProc — Low-Level Keyboard Procedure
# Тип колбэка, который принимает WinAPI при установке WH_KEYBOARD_LL.
# Вызывается на каждое событие клавиатуры (до доставки в окна).
LowLevelKeyboardProc = ctypes.WINFUNCTYPE(
    LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM
)

# ---- SetWindowsHookExW — установка системного хука (Wide/Unicode-версия)
# idHook=WH_KEYBOARD_LL, lpfn=наш колбэк, hMod=0 (для LL-хуков DLL не требуется), dwThreadId=0 (глобально)
SetWindowsHookExW = user32.SetWindowsHookExW
SetWindowsHookExW.argtypes = [
    wintypes.INT,
    LowLevelKeyboardProc,
    wintypes.HINSTANCE,
    wintypes.DWORD,
]
SetWindowsHookExW.restype = HHOOK

# ---- UnhookWindowsHookEx — снятие установленного хука по дескриптору
UnhookWindowsHookEx = user32.UnhookWindowsHookEx
UnhookWindowsHookEx.argtypes = [HHOOK]
UnhookWindowsHookEx.restype = wintypes.BOOL

# ---- CallNextHookEx — передача события дальше по цепочке хуков
CallNextHookEx = user32.CallNextHookEx
CallNextHookEx.argtypes = [HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
CallNextHookEx.restype = LRESULT

# ---- GetAsyncKeyState — моментальный опрос состояния клавиши (бит 0x8000 = зажата сейчас)
GetAsyncKeyState = user32.GetAsyncKeyState

# ---- Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


# ---- Вспомогательные функции для разборки lParam из WM.HOTKEY
def LOWORD(dword: int) -> int:
    return dword & 0xFFFF


def HIWORD(dword: int) -> int:
    return (dword >> 16) & 0xFFFF


# ---- KeyboardHook — обёртка над WH_KEYBOARD_LL для ловли CapsLock/ScrollLock
class KeyboardHook:
    def __init__(self, on_caps, on_scroll):
        self.on_caps = on_caps  # колбэк при нажатии CapsLock
        self.on_scroll = on_scroll  # колбэк при нажатии ScrollLock
        self.hook = None  # дескриптор установленного хука (HHOOK)
        self._proc = LowLevelKeyboardProc(
            self._callback
        )  # держим ссылку на колбэк, чтобы GC не удалил

    def install(self):
        hMod = 0  # для WH_KEYBOARD_LL модуль DLL не обязателен
        self.hook = SetWindowsHookExW(WH_KEYBOARD_LL, self._proc, hMod, 0)
        if not self.hook:
            # Диагностика через GetLastError/FormatMessage
            err = ctypes.get_last_error()
            buf = ctypes.create_unicode_buffer(512)
            kernel32.FormatMessageW(0x00001000, None, err, 0, buf, len(buf), None)
            raise OSError(f"SetWindowsHookExW failed, error={err}: {buf.value.strip()}")

    def uninstall(self):
        if self.hook:
            UnhookWindowsHookEx(self.hook)
            self.hook = None

    def _callback(self, nCode, wParam, lParam):
        # nCode == 0 — событие для обработки; wParam — тип (WM.KEYDOWN/WM.SYSKEYDOWN);
        # lParam — указатель на KBDLLHOOKSTRUCT
        if nCode == 0 and wParam in (WM.KEYDOWN, WM.SYSKEYDOWN):
            ks = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            if ks.vkCode == VK.CAPITAL:
                self.on_caps()
            elif ks.vkCode == VK.SCROLL:
                self.on_scroll()
        # Передаём дальше по цепочке хуков
        return CallNextHookEx(None, nCode, wParam, lParam)


# ---- HotkeyFilter — Qt-фильтр нативных событий для перехвата WM.HOTKEY
class HotkeyFilter(QtCore.QAbstractNativeEventFilter):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback  # функция: (hotkey_id, vk, mods) -> None

    def nativeEventFilter(self, eventType: str, message) -> tuple[bool, int]:
        # Под Windows бывают два типа: "windows_generic_MSG" и "windows_dispatcher_MSG"
        if eventType not in ("windows_generic_MSG", "windows_dispatcher_MSG"):
            return False, 0
        msg = wintypes.MSG.from_address(int(message))  # view на структуру MSG из WinAPI
        if msg.message != WM.HOTKEY:
            return False, 0
        hotkey_id = msg.wParam
        vk = LOWORD(msg.lParam)  # LOWORD(lParam) = VK основной клавиши
        mods = HIWORD(msg.lParam)  # HIWORD(lParam) = флаги MOD_*
        self.callback(hotkey_id, vk, mods)
        return True, 0  # сообщение обработано


# ---- SingleInstance — защита от запуска второго экземпляра (через QSharedMemory)
class SingleInstance:
    def __init__(self, key="__codex_hotkey_singleton__"):
        self.mem = QtCore.QSharedMemory(key)

    def is_running(self) -> bool:
        if self.mem.attach():
            self.mem.detach()
            return True
        return False

    def try_lock(self) -> bool:
        return self.mem.create(1)


# ---- MainWindow — простое окно с логом и кнопкой проверки
class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Global Hotkey Demo")
        self.setWindowIcon(
            self.style().standardIcon(
                QtWidgets.QStyle.StandardPixmap.SP_MessageBoxInformation
            )
        )
        lay = QtWidgets.QVBoxLayout(self)
        self.btn = QtWidgets.QPushButton("Проверка")
        self.btn.clicked.connect(self.on_action)
        self.log = QtWidgets.QPlainTextEdit("Начало лога")
        self.log.setReadOnly(True)
        lay.addWidget(self.btn)
        lay.addWidget(self.log)

    @QtCore.pyqtSlot()
    def on_action(self):
        # Здесь может быть полезная реакция на горячую клавишу
        pass

    def append(self, text: str):
        self.log.appendPlainText(text)

    def on_caps(self):
        self.append("CapsLock pressed")

    def on_scroll(self):
        self.append("ScrollLock pressed")


# ---- Tray — иконка в системном трее с меню
class Tray(QtWidgets.QSystemTrayIcon):
    def __init__(self, app, on_quit, on_test):
        icon = app.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_ComputerIcon)
        super().__init__(icon)
        self.setToolTip("Hotkey watcher")
        menu = QtWidgets.QMenu()
        menu.addAction("Тест диалога", on_test)
        menu.addSeparator()
        menu.addAction("Выход", on_quit)
        self.setContextMenu(menu)
        self.show()


# ---- HotkeyApp — главный класс приложения: регистрация хоткея, установка хука, запуск Qt
class HotkeyApp:
    def __init__(self):
        if sys.platform != "win32":
            raise SystemExit("Работает только под Windows.")

        self.app = QtWidgets.QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # Единичный экземпляр
        self.singleton = SingleInstance()
        if self.singleton.is_running():
            QtWidgets.QMessageBox.warning(
                None, "Уже запущено", "Экземпляр уже работает."
            )
            raise SystemExit(0)
        self.singleton.try_lock()

        # UI + трей
        self.ui = MainWindow()
        self.ui.resize(420, 260)
        self.tray = Tray(self.app, self.quit, self.ui.on_action)

        # Глобальный хоткей (Ctrl+H)
        self._register_hotkeys()

        # Перехват WM.HOTKEY в Qt-цикле
        self.filter = HotkeyFilter(self._on_hotkey)
        self.app.installNativeEventFilter(self.filter)

        # Low-level хук только для CapsLock/ScrollLock
        self.khook = KeyboardHook(self.ui.on_caps, self.ui.on_scroll)
        self.khook.install()

        # Очистка при завершении
        self.app.aboutToQuit.connect(self._cleanup)

    def _register_hotkeys(self):
        ok = user32.RegisterHotKey(None, HK_MAIN, MOD.CONTROL | MOD_NOREPEAT, VK.H)
        if not ok:
            QtWidgets.QMessageBox.critical(None, "Ошибка", "RegisterHotKey не удалось.")
            raise SystemExit(1)
        logging.info("Hotkey registered: Ctrl+H (ID=%d)", HK_MAIN)

    def _unregister_hotkeys(self):
        try:
            user32.UnregisterHotKey(None, HK_MAIN)
            logging.info("Hotkey unregistered")
        except Exception:
            logging.exception("UnregisterHotKey failed")

    def _cleanup(self):
        self._unregister_hotkeys()
        self.khook.uninstall()

    def _on_hotkey(self, hotkey_id: int, vk: int, mods: int):
        # Получаем снимок состояний левого/правого Ctrl (best-effort)
        if hotkey_id != HK_MAIN:
            return
        left = bool(GetAsyncKeyState(VK.LCONTROL) & 0x8000)
        right = bool(GetAsyncKeyState(VK.RCONTROL) & 0x8000)
        self.ui.append(
            f"WM.HOTKEY id={hotkey_id} vk=0x{vk:X} mods=0x{mods:X} LCtrl={left} RCtrl={right}"
        )
        self.ui.on_action()

    def run(self):
        self.ui.show()
        return self.app.exec()

    def quit(self):
        self.tray.hide()
        QtWidgets.QApplication.quit()


# ---- Точка входа
def main():
    try:
        app = HotkeyApp()
    except SystemExit as e:
        sys.exit(int(e.code) if hasattr(e, "code") else 0)
    except Exception:
        logging.exception("Fatal error on startup")
        sys.exit(1)
    sys.exit(app.run())


if __name__ == "__main__":
    main()
