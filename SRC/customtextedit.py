from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtCore import Qt

from SRC.signals import signals_bus
from SRC.try_log import log_exceptions
from SRC.constants import C


class CustomTextEdit(QTextEdit):
    """Расширение класса QTextEdit для обработки нажатия специальных клавиш"""

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        """
        Переопределение метода. Перехватываем ввод с клавиатуры.
        Обрабатываем специальные клавиши
        :param event: (QKeyEvent). Событие нажатия клавиши
        :return: None
        """
        if event is None:
            return

        if not self.run_special_key(event):  # Обрабатываем специальные клавиши
            super().keyPressEvent(
                event
            )  # Для остальных клавиш передаём обработку системе

    @staticmethod
    @log_exceptions(C.TEXT_ERROR_CONNECT)
    def run_special_key(event: QKeyEvent) -> bool:
        """Обрабатываем нажатие горячих клавиш кнопок"""
        match event.key():
            case Qt.Key.Key_1:  # Заменить текст
                signals_bus.on_Yes.emit()
            case Qt.Key.Key_Escape:  # Отказ от замены
                signals_bus.on_No.emit()
            case Qt.Key.Key_2:  # Отказ от замены
                signals_bus.on_No.emit()
            case Qt.Key.Key_3:  # Выгрузить программу
                signals_bus.on_Cancel.emit()
            case _:
                return False

        return True
