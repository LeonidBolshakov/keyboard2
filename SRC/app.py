import sys

from PyQt6 import QtWidgets

from SRC.tunelogger import TuneLogger
from SRC.constants import C
from SRC.tray_pay import Tray
from SRC.single_instance import SingleInstance
from SRC.UI.main_window import MainWindow
from SRC.controller import Controller
from SRC.hotkey_win import (
    register_hotkey,
    unregister_hotkey,
    HotkeyFilter,
    MOD_CONTROL,  # Требует нажатия клавиши Ctrl
    MOD_NOREPEAT,  # отключает автоповтор события, если пользователь держит клавишу
)
from llkeyboard import KeyboardHook

VK_H = 0x48  # Код клавиши H
HK_MAIN = 1  # Логический идентификатор горячей клавиши


def main_app():
    if sys.platform != "win32":
        raise SystemExit("Только Windows.")

    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(
        False
    )  # Продолжить жить даже после закрытия всех окон

    # логирование
    TuneLogger().setup_logging()

    # единственный экземпляр
    single = SingleInstance()
    if single.already_running():
        QtWidgets.QMessageBox.warning(None, C.SINGLE_TITLE, C.SINGLE_TEXT)
        return 0
    if not single.claim_ownership():
        QtWidgets.QMessageBox.warning(None, C.SINGLE_TITLE, C.SINGLE_TEXT)
        return 0

    # UI
    ui = MainWindow()
    ui.resize(420, 260)
    ctrl = Controller(ui)

    # Tray
    Tray(
        app,
        on_quit=lambda: QtWidgets.QApplication.quit(),
        actions={"Тест диалога": ui.on_action},
    )

    # Глобальные горячие клавиши
    register_hotkey(HK_MAIN, MOD_CONTROL | MOD_NOREPEAT, VK_H)
    hk_filter = HotkeyFilter(ctrl.on_hotkey)
    app.installNativeEventFilter(hk_filter)

    # Low-level hook Caps/ScrLk
    khook = KeyboardHook(ctrl.on_caps, ctrl.on_scroll)
    khook.install()

    def cleanup():
        unregister_hotkey(HK_MAIN)
        khook.uninstall()

    app.aboutToQuit.connect(cleanup)

    ui.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main_app())
