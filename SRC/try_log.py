from functools import wraps
import logging

logger = logging.getLogger(__name__)


def log_exceptions(_fn=None, *, name: str | None = None, reraise: bool = False):
    # поддержка формы @log_exceptions("текст")
    if _fn is not None and not callable(_fn):
        name = str(_fn)
        _fn = None

    def _decorate(fn):
        @wraps(fn)
        def w(*a, **k):
            try:
                need = fn.__code__.co_argcount
                return fn(*a[:need], **k)
            except Exception:
                logger.exception(name or fn.__qualname__)
                if reraise:
                    raise

        return w

    # @log_exceptions          -> _fn is function
    if callable(_fn):
        return _decorate(_fn)
    # @log_exceptions(...)     -> вернуть декоратор
    return _decorate


#
# # pyqt6_loguru_demo.py
# import sys
# from PyQt6 import QtWidgets, QtCore
# from loguru import logger
#
# # Настройка loguru: консоль WARNING+, файл DEBUG+
# logger.remove()
# logger.add(sys.stderr, level="WARNING", backtrace=True, diagnose=True)
# logger.add(
#     "app.log", level="DEBUG", rotation="1 week", retention="1 month", encoding="utf-8"
# )
#
#
# class Window(QtWidgets.QMainWindow):
#     def __init__(self):
#         super().__init__()
#         btn = QtWidgets.QPushButton("Кликни меня")
#         btn.clicked.connect(self.on_click)  # сигнал clicked(bool)
#         self.setCentralWidget(btn)
#         self.setWindowTitle("PyQt6 + loguru")
#
#     @logger.catch(reraise=False, message="Ошибка в on_click: {exception}")
#     @QtCore.pyqtSlot(bool)  # сигнатура совпадает с clicked(bool)
#     def on_click(self, checked: bool) -> None:
#         logger.info("Нажата кнопка, checked={}", checked)
#         raise RuntimeError("Тестовое исключение из слота")
#
#
# def main():
#     app = QtWidgets.QApplication(sys.argv)
#     w = Window()
#     w.resize(320, 120)
#     w.show()
#     sys.exit(app.exec())
#
#
# if __name__ == "__main__":
#     main()
