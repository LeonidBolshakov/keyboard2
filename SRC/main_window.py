"""Класс организации диалога с пользователем"""

import logging

logger = logging.getLogger(__name__)

from enum import IntEnum
import os

from PyQt6 import uic
from PyQt6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PyQt6.QtCore import Qt, QTimer, QCoreApplication, pyqtBoundSignal

from PyQt6.QtWidgets import QMainWindow, QDialogButtonBox, QPushButton, QMessageBox

from SRC.signals import signals_bus
from SRC.replacetext import ReplaceText
from SRC.customtextedit import CustomTextEdit
from SRC.controller import Controller
from SRC.try_log import log_exceptions
import SRC.functions as f
from SRC.constants import C


class DialogResult(IntEnum):
    EXIT = 0  # завершить / выгрузить программу
    REPLACE = 1  # заменить выделенный текст
    SKIP = 2  # отказ от замены выделенного текста


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
        self.controller = Controller()

        self.init_UI()  # Загружаем файл, сформированный Qt Designer
        self.init_buttons()  # Инициализируем переменные
        self.set_connects()  # Назначаем обработчики событий
        self.set_signals()  # Назначаем обработчики сигналов
        self.custom_UI()  # Делаем пользовательские настройки интерфейса
        self.add_shortcuts()  # Назначаем горячие клавиши

    @log_exceptions
    def closeEvent(self, event: QCloseEvent) -> None:
        """Переопределение метода. Перехватываем закрытие окна Пользователем"""
        # При закрытии окна пользователем сигнализируем об остановке диалога, но программу из памяти не выгружаем
        self.stop_dialogue(DialogResult.EXIT)
        event.ignore()

    def info_start(self):
        """Информирование о начале диалога"""
        logger.info(C.LOGGER_TEXT_LOAD_PROGRAM)
        f.show_message(
            C.TEXT_MESSAGE_START_PROGRAM.format(key=C.HOTKEY_BEGIN_DIALOGUE),
            C.TIME_MESSAGE_START_PROGRAM,
            C.COLOR_MESSAGE_START_PROGRAM,
        )

        # Проверка запуска программы от имени администратора
        logger.info(C.TEXT_NO_ADMIN)
        if not self.is_admin():
            QMessageBox.warning(
                None, C.TITLE_WARNING, C.TEXT_NO_ADMIN, QMessageBox.StandardButton.Ok
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
        self.add_shortcut("sc_yes", "1", signals_bus.on_Yes)
        self.add_shortcut("sc_no", "2", signals_bus.on_No)
        self.add_shortcut("sc_cancel", "3", signals_bus.on_Cancel)
        self.add_shortcut("sc_esc", "Esc", signals_bus.on_No)

    def show_original_text(self, original_text: str) -> None:
        """
        Отображаем текст пользователя
        :param original_text: (str). Текст пользователя
        :return:
        """
        self.txtEditSource.setText(original_text)

    @log_exceptions
    def show_replacements_text(self, replacement_text: str) -> None:
        """Отображаем вариант замены текста."""
        self.txtEditReplace.setText(replacement_text)

    @log_exceptions(C.TEXT_ERROR_REPLACE_TEXT)
    def on_Yes(self):
        """Заменяем выделенный текст предложенным вариантом замены"""
        f.put_text_to_clipboard(self.txtEditReplace.toPlainText())
        self.hide()  # Освобождаем фокус для окна с выделенным текстом
        self.stop_dialogue(DialogResult.REPLACE)

    def on_Cancel(self) -> None:
        """Выгружаем программу"""
        self.stop_dialogue(DialogResult.EXIT)
        logger.info(C.LOGGER_TEXT_UNLOAD_PROGRAM)
        logging.shutdown()
        QTimer.singleShot(0, self.safe_exit)

    @log_exceptions(C.TEXT_ERROR_ON_NO)
    def on_No(self) -> None:
        """Отказ от замены текста"""
        self.stop_dialogue(DialogResult.SKIP)

    def processing_clipboard(self) -> None:
        """Обрабатываем буфер обмена"""
        # 1. Получение выделения
        try:
            text = f.get_selection()
        except (OSError, RuntimeError) as e:  # ожидаемые сбои ОС/окна
            logger.warning(C.TEXT_ERROR_PROCESSING_CLIPBOARD.format(type_error="", e=e))
            return
        except Exception as e:  # неожиданное
            logger.exception(
                C.TEXT_ERROR_PROCESSING_CLIPBOARD.format(type_error="?????", e=e)
            )
            return

        # 2. Пусто — мягко выходим
        if not text:
            return

        # 3. Отрисовка/обновление UI
        try:
            self.show_original_text(text)
        except Exception as e:
            logger.warning(C.TEXT_ERROR_ORIGINAL_TEXT.format(e=e))

    def on_change_original_text(self) -> None:
        self.change_original_text()

    def change_original_text(self) -> None:
        """Изменение оригинального текста"""
        try:
            original_text = self.txtEditSource.toPlainText()
            replacements_text = ReplaceText().swap_keyboard_register(original_text)
            self.show_replacements_text(replacements_text)
        except Exception as e:
            logger.exception(C.TEXT_ERROR_CHANGE_TEXT.format(e=e))

    @log_exceptions(C.TEXT_ERROR_SCROLL)
    def start_dialog(self) -> None:
        """
        Начало работы с всплывающим окном.
        :return: None
        """
        if not self.isHidden():  # Если диалог не закончен - новый не начинаем
            return

        self.info_start_dialog()
        self.working_with_clipboard()
        self.working_with_window()

    def info_start_dialog(self):
        window = f.get_window()  # Получаем активное окно операционной системы
        if window:
            window.activate()  # Поднимаем окно поверх других окон
            title = window.title
        else:
            title = C.TEXT_WINDOW_NOT_FOUND
        logger.info(C.LOGGER_TEXT_START_DIALOGUE.format(title=title))

    def working_with_clipboard(self) -> None:
        # запоминаем буфер обмена для возможного дальнейшего восстановления
        self.old_clipboard_text = f.get_clipboard_text()
        self.processing_clipboard()  # Обрабатываем буфер обмена

    def working_with_window(self) -> None:
        self.setWindowFlag(
            Qt.WindowType.WindowStaysOnTopHint, True
        )  # Поднимаем окно диалога над всеми окнами
        self.show()  # Показываем окно
        # Делаем окно доступным для ввода с клавиатуры
        self.activateWindow()

    @log_exceptions(C.TEXT_ERROR_STOP_DIALOG)
    def stop_dialogue(self, command: DialogResult) -> None:
        self.processing_command(command)
        self.restore_clipboard()
        self.hide()  # Убираем окно с экрана

        logger.info(C.LOGGER_TEXT_STOP_DIALOGUE)

    def processing_command(self, command: DialogResult):
        """
        Выполняем команду, заданную в параметре.
        : command: (int) - Код команды закрытия диалога
        """
        match command:
            case DialogResult.EXIT:  # Выгрузка программы
                pass
            case DialogResult.REPLACE:  # Заменяем выделенный текст
                f.replace_selected_text_and_register()
            case DialogResult.SKIP:  # Отказ от замены текста
                pass
            case _:  # Непредусмотренная команда
                logger.critical(C.TEXT_CRITICAL_ERROR.format(command=command))

    def restore_clipboard(self) -> None:
        # Восстанавливаем первоначальный буфер обмена
        f.put_text_to_clipboard(self.old_clipboard_text)
        logger.info(
            C.LOGGER_TEXT_RESTORED_CLIPBOARD.format(
                clipboard_text=self.old_clipboard_text[: C.CLIPBOARD_LOG_LIMIT]
            )
        )

    @log_exceptions(C.TEXT_ERROR_CONNECT_SIGNAL)
    def set_signals(self) -> None:
        """Связываем сигнал с функцией обработки"""
        signals_bus.on_Yes.connect(self.on_Yes)
        signals_bus.on_No.connect(self.on_No)
        signals_bus.on_Cancel.connect(self.on_Cancel)
        signals_bus.start_dialog.connect(self.start_dialog)

    def add_shortcut(
        self,
        attr_name: str,
        key: str | QKeySequence,
        slot: pyqtBoundSignal,
    ) -> QShortcut:
        """
        Назначение горячей клавиши главного (единственного) окна программы
        :param self:
        :param attr_name: Имя атрибута для сохранения ссылки, что бы не удалил сборщик мусора
        :param key: Текстовок или QKeySequence обозначение клавиши.
        :param slot: Signal, который надо активировать, при нажатии клавиши
        :return: горячая клавиша
        """
        sc = QShortcut(QKeySequence(key), self)
        sc.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        sc.setAutoRepeat(False)
        sc.activated.connect(slot)
        setattr(self, attr_name, sc)  # сохранить ссылку: self.sc_yes и т.п.
        return sc

    @staticmethod
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

    @staticmethod
    def is_admin() -> bool:
        """
        Проверка. Вошли ли в программу с правами администратора
        :return: True - если в программу вошли с правами администратора.
        """
        try:
            os.listdir(r"C:\Windows\Temp")  # Любое действие, требующее прав
            return True
        except PermissionError:
            return False
