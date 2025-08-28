"""Класс организации диалога с пользователем"""

from typing import Callable
import logging

logger = logging.getLogger()

from PyQt6 import uic
from PyQt6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PyQt6.QtCore import Qt, QTimer, QCoreApplication
from PyQt6.QtWidgets import QMainWindow, QDialogButtonBox, QPushButton

from SRC.signals import signals_bus
from SRC.replacetext import ReplaceText
from SRC.customtextedit import CustomTextEdit
import SRC.functions as f
from SRC.constants import C


def safe_exit():
    """
    Корректное завершение приложения Qt.
    Перехватывает ошибки при вызове QCoreApplication.exit().
    """
    try:
        QCoreApplication.exit()
    except Exception as e:
        logger.error(C.TEXT_ERROR_EXIT.format(e=e))
        raise


def add_shortcut(
    self,
    attr_name: str,
    key: str | QKeySequence,
    slot: Callable,
) -> QShortcut:
    sc = QShortcut(QKeySequence(key), self)
    sc.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
    sc.setAutoRepeat(False)
    sc.activated.connect(slot)
    setattr(self, attr_name, sc)  # сохранить ссылку: self.sc_yes и т.п.
    return sc


from functools import wraps


def log_exceptions(name: str | None = None):
    def deco(fn):
        @wraps(fn)
        def w(*a, **k):
            try:
                need = (
                    fn.__code__.co_argcount
                )  # сколько позиционных ждёт fn (включая self)
                return fn(
                    *a[:need], **k
                )  # отбросить, например, checked из clicked(bool)
            except Exception:
                logger.exception(name or fn.__qualname__)

        return w

    return deco


# noinspection PyUnresolvedReferences
class MainWindow(QMainWindow):
    """Класс организации диалога с пользователем"""

    # Переменные класса, определённые в Qt Designer
    txtEditSource: CustomTextEdit
    txtEditReplace: CustomTextEdit
    buttonBox: QDialogButtonBox
    yes_button: QPushButton
    no_button: QPushButton
    cancel_button: QPushButton

    def __init__(self) -> None:
        """Инициализация объекта класса"""
        super().__init__()

        # Информирование о первоначальной загрузке программы
        self.info_start()

        # Объявление имён
        self.old_clipboard_text = ""
        self.clipboard_text = ""
        self.is_restore_clipboard = True

        self.init_UI()  # Загружаем файл, сформированный Qt Designer
        self.init_buttons()  # Инициализируем переменные
        self.set_connects()  # Назначаем обработчики событий
        self.setup_signals()
        self.custom_UI()  # Делаем пользовательские настройки интерфейса
        self.add_shortcuts()  # Назначаем горячие клавиши

    @log_exceptions
    def closeEvent(self, event: QCloseEvent) -> None:
        """Переопределение метода. Перехватываем закрытие окна Пользователем"""
        # При закрытии окна пользователем сигнализируем об остановке диалога, но программу из памяти не выгружаем
        self.stop_dialogue(2)
        event.ignore()

    @staticmethod
    def info_start():
        """Информирование о начале диалога"""
        logging.info(C.LOGGER_TEXT_LOAD_PROGRAM)
        f.show_message(
            C.TEXT_MESSAGE_START_PROGRAM.format(key=C.HOTKEY_BEGIN_DIALOGUE),
            C.TIME_MESSAGE_START_PROGRAM,
            C.COLOR_MESSAGE_START_PROGRAM,
        )

    def init_UI(self) -> None:
        """Загрузка UI и атрибутов полей в объект класса"""
        ui_path = f.get_exe_directory() / C.UI_PATH_FROM_EXE
        if not ui_path.is_file():
            raise FileNotFoundError(ui_path)
        try:
            uic.loadUi(str(ui_path), self)
        except Exception:
            logger.exception(C.TEXT_ERROR_LOAD_UI.format(ui_path=ui_path))
            raise

    def init_buttons(self):
        """Присваиваем значения переменным программы"""
        self.yes_button = self.buttonBox.button(QDialogButtonBox.StandardButton.Yes)
        self.no_button = self.buttonBox.button(QDialogButtonBox.StandardButton.No)
        self.cancel_button = self.buttonBox.button(
            QDialogButtonBox.StandardButton.Cancel
        )

    @log_exceptions(C.TEXT_ERROR_CONNECT)
    def set_connects(self):
        """Назначаем обработчики"""

        # Обработчик событий для клика кнопок
        self.yes_button.clicked.connect(self.on_Yes)
        self.no_button.clicked.connect(self.on_No)
        self.cancel_button.clicked.connect(self.on_Cancel)

        # Обработчик изменения оригинального текста
        self.txtEditSource.textChanged.connect(self.change_original_text)

    @log_exceptions(C.TEXT_ERROR_CUSTOM_UI)
    def custom_UI(self):
        """Пользовательская настройка интерфейса"""
        # Устанавливаем размеры, стили, свойства и названия кнопок
        f.making_button_settings(self.yes_button, C.TEXT_YES_BUTTON, C.QSS_YES)
        f.making_button_settings(self.no_button, C.TEXT_NO_BUTTON, C.QSS_NO)
        f.making_button_settings(self.cancel_button, C.TEXT_CANCEL_BUTTON)

        # Устанавливаем стили текстовых полей
        self.txtEditSource.setStyleSheet(C.QSS_TEXT)
        self.txtEditReplace.setStyleSheet(C.QSS_TEXT)

        # Кнопка Yes будет срабатывать по Enter
        self.yes_button.setDefault(True)

        # установить фокус в первое поле после показа окна
        QTimer.singleShot(0, self.txtEditSource.setFocus)

    def add_shortcuts(self) -> None:
        add_shortcut(self, "sc_yes", "1", signals_bus.on_Yes)
        add_shortcut(self, "sc_no", "2", signals_bus.on_No)
        add_shortcut(self, "sc_cancel", "3", signals_bus.on_Cancel)
        add_shortcut(self, "sc_esc", "Esc", signals_bus.on_No)

    def show_original_text(self, original_text: str) -> None:
        """
        Отображаем текст пользователя
        :param original_text: (str). Текст пользователя
        :return:
        """
        self.txtEditSource.setText(original_text)

    @log_exceptions("show_replacements_text")
    def show_replacements_text(self, replacement_text: str) -> None:
        """Отображаем вариант замены текста."""
        self.txtEditReplace.setText(replacement_text)

    @log_exceptions(C.TEXT_ERROR_REPLACE_TEXT)
    def on_Yes(self):
        """Заменяем выделенный текст предложенным вариантом замены"""
        f.put_text_to_clipboard(self.txtEditReplace.toPlainText())
        self.hide()  # Освобождаем фокус для окна с выделенным текстом
        self.stop_dialogue(1)

    @staticmethod
    def on_Cancel() -> None:
        """Выгружаем программу"""
        logger.info(C.LOGGER_TEXT_UNLOAD_PROGRAM)
        QTimer.singleShot(0, safe_exit)

    @log_exceptions(C.TEXT_ERROR_ON_NO)
    def on_No(self) -> None:
        """Отказ от замены текста"""
        self.stop_dialogue(2)

    def processing_clipboard(self) -> None:
        """Обрабатываем буфер обмена"""

        # 1. Получение выделения
        try:
            text = f.get_selection()
        except (OSError, RuntimeError) as e:  # ожидаемые сбои ОС/окна
            logger.warning(
                C.TEXT_ERROR_PROCESSING_CLIPBOARD.format(
                    type_error=C.TEXT_ERROR_PROCESSING_CLIPBOARD_1, e=e
                )
            )
            return
        except Exception as e:  # неожиданное
            logger.exception(
                C.TEXT_ERROR_PROCESSING_CLIPBOARD.format(type_error="?????", e=e)
            )
            return

        # 2. Пусто — мягко выходим
        if not text:
            self.is_restore_clipboard = False
            return

        # 3. Отрисовка/обновление UI
        try:
            self.show_original_text(text)
        except Exception as e:
            logger.warning(C.TEXT_ERROR_ORIGINAL_TEXT.format(e=e))
        self.is_restore_clipboard = False

    def change_original_text(self) -> None:
        """Изменение оригинального текста"""
        try:
            original_text = self.txtEditSource.toPlainText()
            replacements_text = ReplaceText().swap_keyboard_register(original_text)
            self.show_replacements_text(replacements_text)
        except Exception as e:
            logger.exception(C.TEXT_ERROR_CHANGE_TEXT.format(e=e))

    def start_dialogue(self) -> None:
        """
        Начало работы с всплывающим окном.
        :return: None
        """
        if not self.isHidden():  # Если диалог не закончен - новый не начинаем
            return
        try:
            window = f.get_window()  # Получаем активное окно операционной системы
            title = window.title if window else C.TEXT_WINDOW_NOT_FOUND
            logger.info(C.LOGGER_TEXT_START_DIALOGUE.format(title=title))
            if window:
                window.activate()  # Поднимаем окно поверх других окон
                title = window.title
            else:
                title = C.TEXT_WINDOW_NOT_FOUND

            # запоминаем буфер обмена для возможного дальнейшего восстановления
            try:
                self.old_clipboard_text = f.get_clipboard_text()
            except Exception as e:
                logger.exception("clipboard read failed")
                self.old_clipboard_text = ""

            self.is_restore_clipboard = True
            self.processing_clipboard()  # Обрабатываем буфер обмена
            self.setWindowFlag(
                Qt.WindowType.WindowStaysOnTopHint, True
            )  # Поднимаем окно диалога над всеми окнами
            self.show()  # Показываем окно
            # Делаем окно доступным для ввода с клавиатуры
            self.activateWindow()
        except Exception as e:
            logger.exception(C.TEXT_ERROR_SCROLL.format(e=e))

    def stop_dialogue(self, command: int) -> None:
        """
        Выполняем команду, заданную в параметре.
        : command: (int) - Код команды закрытия диалога
        """
        try:
            # Обрабатываем команду
            match command:
                case 0:  # Выгрузка программы
                    pass
                case 1:  # Заменяем выделенный текст
                    try:
                        f.replace_selected_text()
                    except Exception as e:
                        logger.exception(e)
                case 2:  # Отказ от замены текста
                    pass
                case _:  # Непредусмотренная команда
                    logger.critical(C.TEXT_CRITICAL_ERROR.format(command=self.command))

            # Если буфер обмена не требуется для завершения действий Пользователя,
            # то восстанавливаем первоначальный буфер обмена
            if self.is_restore_clipboard:
                try:
                    f.put_text_to_clipboard(self.old_clipboard_text)
                    logger.info(
                        C.LOGGER_TEXT_RESTORED_CLIPBOARD.format(
                            clipboard_text=self.old_clipboard_text
                        )
                    )
                except Exception as e:
                    logger.exception(e)
        except Exception as e:
            logger.exception(e)
        finally:
            try:
                self.hide()  # Убираем окно с экрана
            except Exception:
                pass
            logger.info(C.LOGGER_TEXT_STOP_DIALOGUE)

    @log_exceptions(C.TEXT_ERROR_CONNECT_SIGNAL)
    def setup_signals(self) -> None:
        """Связываем сигнал с функцией обработки"""
        signals_bus.on_Yes.connect(self.on_Yes)
        signals_bus.on_No.connect(self.on_No)
        signals_bus.on_Cancel.connect(self.on_Cancel)
