# FILE: controller.py
from PyQt6 import QtWidgets
import ctypes

GetAsyncKeyState = ctypes.windll.user32.GetAsyncKeyState
VK_LCONTROL, VK_RCONTROL = 0xA2, 0xA3


class Controller:
    """Не знает WinAPI-деталей регистрации. Только реакции."""

    def __init__(self, ui):
        self.ui = ui

    def on_hotkey(self, hkid: int, vk: int, mods: int):
        left = bool(GetAsyncKeyState(VK_LCONTROL) & 0x8000)
        right = bool(GetAsyncKeyState(VK_RCONTROL) & 0x8000)
        self.ui.append(
            f"WM_HOTKEY id={hkid} vk=0x{vk:X} mods=0x{mods:X} L={left} R={right}"
        )
        QtWidgets.QMessageBox.information(
            self.ui, "Hotkey", "Сработал глобальный хоткей"
        )

    def on_caps(self):
        self.ui.append("CapsLock pressed")

    def on_scroll(self):
        self.ui.append("ScrollLock pressed")
