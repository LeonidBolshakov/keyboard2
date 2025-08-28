"""
Модуль system_tray.py

Назначение:
    Управление иконкой приложения в системном трее Windows.

Содержимое:
    - Класс Tray, наследник QSystemTrayIcon.
    - Создание иконки в трее.
    - Формирование контекстного меню с пользовательскими действиями.
    - Обработка нажатия пункта "Выход" для завершения приложения.
"""

from typing import Callable
import logging

logger = logging.getLogger(__name__)

from PyQt6 import QtWidgets

from SRC.constants import C


class Tray(QtWidgets.QSystemTrayIcon):
    """Системный трей приложения.

    Отвечает за:
    - Отображение иконки.
    - Формирование контекстного меню.
    - Вызов обработчиков действий и выхода.
    """

    def __init__(
        self,
        app: QtWidgets.QApplication,
        on_quit: Callable[[], None],
        actions: dict[str, Callable[[], None]],
    ):
        """Создаёт трей, меню и задаёт иконку.

        Параметры
        ---------
        app : QtWidgets.QApplication
        Экземпляр приложения.
        on_quit : Callable[[], None]
        Обработчик выхода.
        actions : dict[str, Callable[[], None]]
        Дополнительные элементы меню вида {"Название": функция}.
        """
        super().__init__(app)  # базовый конструктор

        self._create_icon(app)
        menu = self._create_menu(on_quit, actions)
        self.setContextMenu(menu)
        self.setVisible(True)

    def _create_menu(
        self, on_quit: Callable[[], None], actions: dict[str, Callable[[], None]]
    ) -> QtWidgets.QMenu:
        """
        Создание меню трея

        :param on_quit : Callable[[], None]
            Обработчик выхода.
        :param actions dict[str, Callable[[], None]]
            Дополнительные элементы меню вида {"Название": функция}

        :return: QtWidgets.QMenu - Меню трея.
        """
        menu = QtWidgets.QMenu()

        for text, handler in actions.items():
            act = menu.addAction(text)
            try:
                act.triggered.connect(handler)
            except Exception as e:
                logger.error(C.TEXT_ERROR_CONNECT_SIGNAL)

        quit_action = menu.addAction("Выход")
        try:
            quit_action.triggered.connect(on_quit)
        except Exception as e:
            logger.error(C.TEXT_ERROR_CONNECT_SIGNAL)
        finally:
            return menu

    def _create_icon(self, app: QtWidgets.QApplication) -> None:
        """
        Создание иконки меню

        :param app: QApplication

        :return: None
        """
        style = app.style()
        if style is not None:
            icon = style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_ComputerIcon)
            self.setIcon(icon)
