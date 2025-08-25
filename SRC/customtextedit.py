from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtCore import Qt

from SRC.signals import signals_bus


class CustomTextEdit(QTextEdit):
    """Расширение класса QTextEdit для обработки нажатия специальных клавиш"""

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        Переопределение метода. Перехватываем ввод с клавиатуры.
        Обрабатываем специальные клавиши
        :param event: (QKeyEvent). Событие нажатия клавиши
        :return: None
        """
        if not self.run_special_key(event):  # Обрабатываем специальные клавиши
            super().keyPressEvent(
                event
            )  # Для остальных клавиш передаём обработку системе

    @staticmethod
    def run_special_key(event: QKeyEvent) -> bool:
        """Обрабатываем нажатие горячих клавиш кнопок"""
        match event.key():
            case Qt.Key.Key_1:  # Заменять текст
                try:
                    signals_bus.on_Yes.emit()
                except Exception as e:
                    print('Ошибка при emit сигнала:', e)
            case Qt.Key.Key_Escape:  # Отказ от замены
                try:
                    signals_bus.on_No.emit()
                except Exception as e:
                    print('Ошибка при emit сигнала:', e)
            case Qt.Key.Key_2:  # Отказ от замены
                try:
                    signals_bus.on_No.emit()
                except Exception as e:
                    print('Ошибка при emit сигнала:', e)
            case Qt.Key.Key_3:  # Выгрузить программу
                try:
                    signals_bus.on_Cancel.emit()
                except Exception as e:
                    print('Ошибка при emit сигнала:', e)
            case _:
                return False

        return True