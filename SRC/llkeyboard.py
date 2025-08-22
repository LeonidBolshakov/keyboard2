# FILE: llkeyboard.py
# Low-level hook для одиночных клавиш (CapsLock/ScrollLock)
import ctypes
from ctypes import wintypes

WH_KEYBOARD_LL = 13
WM_KEYDOWN, WM_SYSKEYDOWN = 0x0100, 0x0104
VK_CAPITAL, VK_SCROLL = 0x14, 0x91

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

PTR_64 = ctypes.sizeof(ctypes.c_void_p) == 8
ULONG_PTR = getattr(
    wintypes, "ULONG_PTR", ctypes.c_ulonglong if PTR_64 else ctypes.c_ulong
)
LRESULT = getattr(wintypes, "LRESULT", ctypes.c_longlong if PTR_64 else ctypes.c_long)
HHOOK = getattr(wintypes, "HHOOK", ctypes.c_void_p)


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


LowLevelKeyboardProc = ctypes.WINFUNCTYPE(
    LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM
)

SetWindowsHookExW = user32.SetWindowsHookExW
SetWindowsHookExW.argtypes = [
    wintypes.INT,
    LowLevelKeyboardProc,
    wintypes.HINSTANCE,
    wintypes.DWORD,
]
SetWindowsHookExW.restype = HHOOK
UnhookWindowsHookEx = user32.UnhookWindowsHookEx
UnhookWindowsHookEx.argtypes = [HHOOK]
UnhookWindowsHookEx.restype = wintypes.BOOL
CallNextHookEx = user32.CallNextHookEx
CallNextHookEx.argtypes = [HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
CallNextHookEx.restype = LRESULT


class KeyboardHook:
    """on_caps(), on_scroll() — колбэки на KEYDOWN Caps/Scroll."""

    def __init__(self, on_caps, on_scroll):
        self.on_caps = on_caps
        self.on_scroll = on_scroll
        self.hook = None
        self._proc = LowLevelKeyboardProc(self._callback)

    def install(self):
        self.hook = SetWindowsHookExW(WH_KEYBOARD_LL, self._proc, 0, 0)
        if not self.hook:
            err = ctypes.get_last_error()
            buf = ctypes.create_unicode_buffer(512)
            kernel32.FormatMessageW(0x00001000, None, err, 0, buf, len(buf), None)
            raise OSError(f"SetWindowsHookExW failed, error={err}: {buf.value.strip()}")

    def uninstall(self):
        if self.hook:
            UnhookWindowsHookEx(self.hook)
            self.hook = None

    def _callback(self, nCode, wParam, lParam):
        if nCode == 0 and wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
            ks = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            if ks.vkCode == VK_CAPITAL:
                self.on_caps()
            elif ks.vkCode == VK_SCROLL:
                self.on_scroll()
        return CallNextHookEx(None, nCode, wParam, lParam)
