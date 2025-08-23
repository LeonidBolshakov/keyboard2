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
from PyQt6 import QtWidgets


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

        # иконка трея
        style = app.style()
        if style is not None:
            icon = style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_ComputerIcon)
            self.setIcon(icon)

        # меню трея
        menu = QtWidgets.QMenu()
        for text, handler in actions.items():
            act = menu.addAction(text)
            act.triggered.connect(handler)

        quit_action = menu.addAction("Выход")
        quit_action.triggered.connect(on_quit)

        self.setContextMenu(menu)
        self.setVisible(True)
