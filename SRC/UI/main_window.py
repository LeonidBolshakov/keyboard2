# FILE: ui/main_window.py
from PyQt6 import QtWidgets, QtCore


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Global Hotkey Demo")
        lay = QtWidgets.QVBoxLayout(self)
        self.btn = QtWidgets.QPushButton("Проверка")
        # self.btn.clicked.connect(self.on_action)
        self.log = QtWidgets.QPlainTextEdit("Начало лога")
        self.log.setReadOnly(True)
        lay.addWidget(self.btn)
        lay.addWidget(self.log)
        self.resize(420, 260)

    @QtCore.pyqtSlot()
    def on_action(self):
        QtWidgets.QMessageBox.information(self, "Действие", "Сработал хоткей")

    def append(self, text: str):
        self.log.appendPlainText(text)
