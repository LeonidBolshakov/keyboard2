# ---- HotkeyApp — главный класс приложения: регистрация хоткея, установка хука, запуск Qt
import sys
import logging
from PyQt6 import QtWidgets


class HotkeyApp:
    def __init__(self):
        if sys.platform != "win32":
            raise SystemExit("Работает только под Windows.")

        self.app = QtWidgets.QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # Единичный экземпляр
        self.singleton = SingleInstance()
        if self.singleton.already_running():
            QtWidgets.QMessageBox.warning(
                None, "Уже запущено", "Экземпляр уже работает."
            )
            raise SystemExit(0)
        self.singleton.claim_ownership()

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
