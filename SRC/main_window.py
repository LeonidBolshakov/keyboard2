"""Класс организации диалога с пользователем"""

import logging

logger = logging.getLogger()

from PyQt6 import uic
from PyQt6.QtGui import QKeyEvent, QCloseEvent
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
        logger.error("Ошибка выхода: %s", e)


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

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        Переопределение метода. Перехватываем ввод с клавиатуры.
        Обрабатываем специальные клавиши
        :param event: (QKeyEvent). Событие нажатия клавиши
        :return: None
        """
        try:
            if not f.run_special_key(event):  # Обрабатываем специальные клавиши
                super().keyPressEvent(
                    event
                )  # Для остальных клавиш передаём обработку системе
        except Exception as e:
            logger.exception(e)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Переопределение метода. Перехватываем закрытие окна Пользователем"""
        # При закрытии окна пользователем сигнализируем об остановке диалога, но программу из памяти не выгружаем
        try:
            self.stop_dialogue(2)
            event.ignore()
        except Exception as e:
            logger.exception(e)

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
        try:
            ui_config_abs_path = f.get_exe_directory() / C.UI_PATH_FROM_EXE
            uic.loadUi(ui_config_abs_path, self)
        except Exception as e:
            logger.error(C.TEXT_ERROR_LOAD_UI.format(e=e))
            raise RuntimeError(C.TEXT_ERROR_LOAD_UI.format(e=e)) from e

    def init_buttons(self):
        """Присваиваем значения переменным программы"""
        try:
            self.yes_button = self.buttonBox.button(QDialogButtonBox.StandardButton.Yes)
            self.no_button = self.buttonBox.button(QDialogButtonBox.StandardButton.No)
            self.cancel_button = self.buttonBox.button(
                QDialogButtonBox.StandardButton.Cancel
            )
        except Exception as e:
            logger.error(C.TEXT_ERROR_INIT_BUTTON.format(e=e))
            raise RuntimeError(C.TEXT_ERROR_INIT_BUTTON.format(e=e)) from e

    def set_connects(self):
        """Назначаем обработчики"""
        try:
            # Обработчик событий для клика кнопок
            try:
                self.yes_button.clicked.connect(self.on_Yes)
            except Exception as e:
                print("Ошибка подключения сигнала:", e)
            try:
                self.no_button.clicked.connect(self.on_No)
            except Exception as e:
                print("Ошибка подключения сигнала:", e)
            try:
                self.cancel_button.clicked.connect(self.on_Cancel)
            except Exception as e:
                print("Ошибка подключения сигнала:", e)

            # Обработчик изменения копии оригинального текста
            try:
                self.txtEditSource.textChanged.connect(self.change_original_text)
            except Exception as e:
                print("Ошибка подключения сигнала:", e)
        except Exception as e:
            logger.error(C.TEXT_ERROR_CONNECT.format(e=e))
            raise RuntimeError(C.TEXT_ERROR_CONNECT.format(e=e)) from e

    def custom_UI(self):
        """Пользовательская настройка интерфейса"""
        try:
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
            QTimer.singleShot(0, lambda: self.txtEditSource.setFocus())
        except Exception as e:
            logger.error(C.TEXT_ERROR_CUSTOM_UI.format(e=e))
            raise RuntimeError(C.TEXT_ERROR_CUSTOM_UI.format(e=e)) from e

    def put_original_text(self, original_text: str) -> None:
        """
        Отображаем текст пользователя
        :param original_text: (str)/ текст пользователя
        :return:
        """
        try:
            self.txtEditSource.setText(original_text)
        except Exception as e:
            logger.error(C.TEXT_ERROR_PUT_ORIGINAL_TEXT.format(e=e))

    def show_replacements_text(self, replacement_text: str) -> None:
        """Отображаем вариант замены текста."""
        try:
            # ReplaceText может бросить исключение, страхуемся
            self.txtEditReplace.setText(replacement_text)
        except Exception as e:
            # записываем стек в лог и подставляем исходный текст как fallback
            logger.exception(e)
            try:
                self.txtEditReplace.setText(replacement_option_text)
            except Exception:
                pass

    def on_Yes(self):
        """Заменяем выделенный текст предложенным вариантом замены"""
        try:
            f.put_text_to_clipboard(self.txtEditReplace.toPlainText())
            self.hide()  # Освобождаем фокус для окна с выделенным текстом
            self.stop_dialogue(1)
        except Exception as e:
            logger.error(C.TEXT_ERROR_REPLACE_TEXT.format(e=e))

    @staticmethod
    def on_Cancel() -> None:
        """Выгружаем программу"""
        logger.info(C.LOGGER_TEXT_UNLOAD_PROGRAM)
        QTimer.singleShot(0, lambda: safe_exit())

    def on_No(self) -> None:
        """Отказ от замены текста"""
        try:
            self.stop_dialogue(2)
        except Exception as e:
            logger.exception(e)

    def processing_clipboard(self) -> None:
        """Обрабатываем буфер обмена"""
        try:
            clipboard_text = f.get_selection()

            # Если текст не выделен. Оставляем возможность вручную вставить его с помощью Ctrl_V
            if not clipboard_text:
                self.is_restore_clipboard = False

            self.put_original_text(clipboard_text)  # Отображаем обрабатываемый текст
        except Exception as e:
            logger.error(C.TEXT_ERROR_PROCESSING_CLIPBOARD.format(e=e))

    def change_original_text(self) -> None:
        """Изменение оригинального текста"""
        try:
            original_text = self.txtEditSource.toPlainText()
            replacements_text = ReplaceText().swap_keyboard_register(original_text)
            self.show_replacements_text(replacements_text)
        except Exception as e:
            logger.exception(e)

    def start_dialogue(self) -> None:
        """
        Начало работы с всплывающим окном.
        :return: None
        """
        try:
            if not self.isHidden():  # Если диалог не закончен - новый не начинаем
                return

            window = f.get_window()  # Получаем активное окно операционной системы
            if window:
                window.activate()  # Поднимаем окно поверх других окон
                title = window.title
            else:
                title = C.TEXT_WINDOW_NOT_FOUND

            logger.info(C.LOGGER_TEXT_START_DIALOGUE.format(title=title))
            # запоминаем буфер обмена для возможного дальнейшего восстановления
            try:
                self.old_clipboard_text = f.get_clipboard_text()
            except Exception as e:
                logger.exception(e)
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
            logger.exception(e)

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
            logger.info(f"{C.LOGGER_TEXT_STOP_DIALOGUE}")

    def setup_signals(self) -> None:
        """Связываем сигнал с функцией обработки"""
        try:
            try:
                signals_bus.on_Yes.connect(self.on_Yes)
            except Exception as e:
                print("Ошибка подключения сигнала:", e)
            try:
                signals_bus.on_No.connect(self.on_No)
            except Exception as e:
                print("Ошибка подключения сигнала:", e)
            try:
                signals_bus.on_Cancel.connect(self.on_Cancel)
            except Exception as e:
                print("Ошибка подключения сигнала:", e)
        except Exception as e:
            logger.exception(e)
