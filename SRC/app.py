"""GUI‑приложение на PyQt6 с системным треем, глобальными горячими клавишами и блокировкой
второго экземпляра.

Назначение модуля
-----------------
Запускает главный цикл Qt, создаёт основное окно, системный трей и регистрирует
глобальные горячие клавиши. Следит, чтобы приложение существовало в одном
экземпляре.

Ключевые элементы
-----------------
- :class:`MainApp` — объединяет инициализацию Qt, UI, контроллера, трея,
  глобальных и низкоуровневых горячих клавиш.
- Глобальные константы :data:`VK_H` и :data:`HK_MAIN` — код клавиши и логический
  идентификатор горячей клавиши Ctrl+H.

Зависимости
-----------
- PyQt6
- Внутренние модули: ``SRC.constants``, ``SRC.system_tray``, ``SRC.single_instance``,
  ``SRC.UI.main_window``, ``SRC.controller``, ``SRC.hotkey_win``, ``ll_keyboard``.

Примечание по завершению
------------------------
Слот ``cleanup`` подключён к сигналу ``aboutToQuit``. Он не получает аргументов
от Qt, поэтому параметр ``hook`` объявлен как ``Optional`` и безопасно
обрабатывается внутри метода.
"""

from __future__ import annotations

import sys
import logging

from PyQt6 import QtWidgets

from SRC.constants import C
from SRC.system_tray import Tray
from SRC.single_instance import SingleInstance
from SRC.UI.main_window import MainWindow
from SRC.controller import Controller
from SRC.hotkey_win import (
    register_hotkey,
    unregister_hotkey,
    HotkeyFilter,
    MOD_CONTROL,  # Требует нажатия клавиши Ctrl
    MOD_NOREPEAT,  # Отключает автоповтор события, если пользователь держит клавишу
)
from ll_keyboard import KeyboardHook, VK_CAPITAL, VK_SCROLL


# Код виртуальной клавиши и ID горячих клавиш
VK_H: int = 0x48  # Код клавиши H
HK_MAIN: int = 1  # Логический идентификатор горячей клавиши

logger = logging.getLogger(__name__)


class MainApp:
    """Точка входа и жизненный цикл приложения.

    Отвечает за:
    - Создание ``QApplication`` и главного окна.
    - Регистрацию системного трея и действий.
    - Регистрацию глобальных и низкоуровневых горячих клавиш.
    - Гарантию единственного экземпляра.
    """

    def __init__(self) -> None:
        """Готовит инфраструктуру: ``QApplication``, UI и контроллер."""
        self.app: QtWidgets.QApplication = self.create_app()
        self.ui: MainWindow = MainWindow()
        self.ctrl: Controller = Controller(self.ui)
        self.hk_filter = HotkeyFilter(self.ctrl.on_hotkey)
        self._low_level_hook: KeyboardHook | None = None

    def main_app(self):
        """Запускает приложение.

        Порядок действий:
        1. Проверка платформы и единственности экземпляра.
        2. Инициализация трея.
        3. Регистрация горячих клавиш.
        4. Показ главного окна и вход в цикл событий.

        Returns
        -------
        int
            Код завершения ``QApplication.exec()``.
        """
        if not self.can_continue():
            raise SystemExit(1)

        self.tray()
        self.global_hotkey()
        self.single_hotkeys()

        self.ui.show()
        return self.app.exec()

    def can_continue(self) -> bool:
        """Проверяет совместимость платформы и отсутствие второго экземпляра.

        Returns
        -------
        bool
            ``True`` если можно продолжать, иначе ``False``.
        """
        if sys.platform != "win32":
            logger.critical("Данная программа выполняется только под Windows!")
            raise SystemExit(1)

        # единственный экземпляр
        if not self.single_copy():
            return False
        return True

    def create_app(self) -> QtWidgets.QApplication:
        """Создаёт и настраивает ``QApplication``.

        Возвращает объект приложения, отключает авто‑выход при закрытии всех
        окон, подключает обработчик завершения.
        """
        app = QtWidgets.QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(
            False
        )  # Оставляем app в памяти даже при закрытии всех окон
        app.aboutToQuit.connect(self.cleanup)  # type: ignore[arg-type]
        return app

    def tray(self) -> None:
        """Создаёт системный трей и регистрирует действия меню."""
        Tray(
            self.app,
            on_quit=self.do_quit,
            actions={"Тест диалога": self.ui.on_action},
        )

    def global_hotkey(self) -> None:
        """Регистрирует глобальную горячую клавишу Ctrl+H и фильтр нативных событий."""
        register_hotkey(HK_MAIN, MOD_CONTROL | MOD_NOREPEAT, VK_H)
        self.app.installNativeEventFilter(self.hk_filter)

    def single_hotkeys(self) -> None:
        """Устанавливает низкоуровневый перехватчик CapsLock/ScrollLock."""

        hook = KeyboardHook(
            {
                VK_CAPITAL: self.ctrl.on_caps,
                VK_SCROLL: self.ctrl.on_scroll,
            }
        )
        hook.install()
        self._low_level_hook = hook

    def cleanup(self) -> None:
        """Освобождает ресурсы перед завершением приложения"""

        unregister_hotkey(HK_MAIN)
        hook = self._low_level_hook
        if hook is not None:
            hook.uninstall()

    def do_quit(self) -> None:
        """Корректно завершает цикл Qt."""
        QtWidgets.QApplication.quit()

    def single_copy(self) -> bool:
        """Гарантирует запуск единственного экземпляра приложения.

        Returns
        -------
        bool
            ``True`` если владение получено. Иначе ``False`` и выводится
            диагностическое сообщение в лог.
        """
        single = SingleInstance()

        if single.already_running():
            logger.info(C.SINGLE_TEXT)
            return False

        if (
            not single.claim_ownership()
        ):  # Проиграл в конкуренции при одновременном запуске с другой программой
            logger.info(C.SINGLE_TEXT)
            return False

        return True


if __name__ == "__main__":
    sys.exit(MainApp().main_app())
