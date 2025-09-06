"""GUI приложение на PyQt6 с системным треем, глобальными и одиночными горячими клавишами и
блокировкой запуска второго экземпляра программы

Назначение модуля
-----------------
запускает главный цикл Qt, создаёт основное окно, системный трей и регистрирует
глобальные и одиночные горячие клавиши.
Следит, чтобы приложение существовало в одном экземпляре.

Ключевые элементы
-----------------
- :class:`StartApp` — объединяет инициализацию Qt, UI, контроллера, трея,
  глобальных и низкоуровневых горячих клавиш.

Зависимости
-----------
- PyQt6
- Внутренние модули: ``SRC.constants``, ``SRC.system_tray``, ``SRC.single_instance``,
  ``SRC.UI.main_window``, ``SRC.controller``, ``SRC.hotkey_win``.

Примечание по завершению
------------------------
Слот ``cleanup`` подключён к сигналу ``aboutToQuit``. Он не получает аргументов
от Qt, поэтому параметр ``hook`` объявлен как ``Optional`` и безопасно
обрабатывается внутри метода.
"""

from __future__ import annotations

import sys
import logging

from PyQt6.QtCore import QObject

logger = logging.getLogger(__name__)

from PyQt6 import QtWidgets

import SRC.functions as f
from SRC.system_tray import Tray
from SRC.single_instance import SingleInstance
from SRC.main_window import MainWindow
from SRC.windows_hotkeys import HotkeyFilter
from SRC.controller import Controller
from SRC.try_log import log_exceptions
from SRC.constants import C


class StartApp(QObject):
    """жизненный цикл приложения.

    Отвечает за:
    - Создание ``QApplication`` и главного окна.
    - Регистрацию системного трея и действий.
    - Регистрацию глобальных и низкоуровневых горячих клавиш.
    - Гарантию единственного экземпляра.
    """

    def __init__(self) -> None:
        """
        Проверка платформы и единственности экземпляра.
        Готовит инфраструктуру: ``QApplication``, UI и контроллер.
        """
        super().__init__()

        self.app = self.create_app()
        self.single = SingleInstance()
        if not self.can_we_continue():
            raise SystemExit(1)
        self.ui = MainWindow()
        self.control = Controller()
        self.hk_filter = HotkeyFilter(self.control.on_hotkey)
        self.app.installNativeEventFilter(self.hk_filter)

    @log_exceptions
    def main_app(self) -> int:
        """Запускает приложение.

        Порядок действий:
        1. Регистрация горячих клавиш.
        2. Подготовка к выходу
        3. Инициализация трея.
        4. Вход в цикл событий.

        Returns
        int
            Код завершения ``QApplication.exec()``.
        """

        _ = int(self.ui.winId())
        self.control.register_global_hotkeys()
        self.control.set_single_hotkeys()
        self.connect_to_quit()
        self.create_tray()

        return self.app.exec()  # Вход в цикл событий

    def can_we_continue(self) -> bool:
        """Проверяет совместимость платформы и отсутствие второго экземпляра.

        Returns
        bool
            True если можно продолжать, иначе False.
        """
        if sys.platform != "win32":
            logger.critical("Данная программа выполняется только под Windows!")
            raise SystemExit(1)

        # единственный экземпляр
        if self.single.already_running():
            f.show_message(  # Сообщение о том, что программа уже загружена
                C.TEXT_MESSAGE_NO_START_PROGRAM,
                C.TIME_MESSAGE_NO_START_PROGRAM,
                C.COLOR_MESSAGE_NO_START_PROGRAM,
            )
            return False
        return True

    @log_exceptions(C.TEXT_ERROR_CONNECT_CLEANUP)
    def connect_to_quit(self) -> None:
        """Привязывает программу, которая по окончанию работы освобождает ресурсы"""
        self.app.aboutToQuit.connect(self.cleanup)  # type: ignore[arg-type]

    def cleanup(self) -> None:
        """Очистка ресурсов"""
        self.single.cleanup()
        self.control.cleanup()

    @log_exceptions(C.TEXT_ERROR_CREATE_APP)
    def create_app(self) -> QtWidgets.QApplication:
        """Создаёт и настраивает ``QApplication``.

        Возвращает объект приложения, отключает авто‑выход при закрытии всех
        окон.
        """

        app = QtWidgets.QApplication(sys.argv)  # type: ignore
        app.setQuitOnLastWindowClosed(
            False
        )  # Оставляем app в памяти даже при закрытии всех окон
        return app

    def create_tray(self) -> None:
        """Создаёт системный трей и регистрирует действия меню."""
        try:
            Tray(
                self.app,
                on_quit=QtWidgets.QApplication.quit,
                actions={"Вызов диалога": self.ui.start_dialog},
            )
        except Exception as e:
            logger.warning(C.TEXT_ERROR_TRAY.format(e=e))


if __name__ == "__main__":
    sys.exit(StartApp().main_app())
