"""Функции, не привязанные к классам"""

import sys
from pathlib import Path
import logging

import pygetwindow as gw  # type: ignore
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QPushButton, QMessageBox, QApplication

import SRC.ll_keyboard as ll_keyboard
from SRC.controller import Controller
from SRC.constants import C

logger = logging.getLogger(__name__)

controller = Controller()


def show_message(
    message: str, show_seconds: int | float = 3, color: QColor = QColor("red")
) -> None:
    """
    Показать информационное сообщение.
    Сообщение можно убрать, нажав на кнопку ОК, клавишу Esc. Или оно само исчезнет через show_seconds секунд
    :param message: (str). Текст сообщения
    :param show_seconds: (int). Время в секундах, после которого сообщение автоматически убирается с экрана
    :param color: (QColor). Цвет сообщения
    :return: None
    """
    msg_box = QMessageBox()

    # Настраиваем окно сообщения
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg_box.setStyleSheet(f"color: {color.name()};")
    # Находим кнопку OK и кликаем её с задержкой
    ok_button = msg_box.button(QMessageBox.StandardButton.Ok)
    if ok_button:
        ok_button.clicked.connect(lambda: None)
        QTimer.singleShot(int(show_seconds * 1000), ok_button.click)

    msg_box.exec()


def making_button_settings(button: QPushButton, text: str, qss: str = "") -> None:
    """
    Настраивает свойства кнопки
    :param button: (QPushButton) - Кнопка
    :param text: (str) - Текст кнопки
    :param qss: (str) - Стиль кнопки
    :return: None
    """
    button.setMinimumWidth(C.MIN_WIDTH_BUTTON)

    if qss:
        button.setStyleSheet(qss + "; " + C.QSS_BUTTON + ";")
    else:
        button.setStyleSheet(C.QSS_BUTTON + ";")

    button.setText(text)

    # Определяем, что если на кнопке установлен фокус, то при нажатии Enter она нажимается.
    button.setAutoDefault(True)


def get_exe_directory() -> Path:
    return (
        Path(sys.executable).parent
        if getattr(sys, "frozen", False)
        else Path(__file__).resolve().parent.parent
    )


def put_text_to_clipboard(text: str) -> None:
    """Записываем текст в буфер обмена"""
    clipboard = QApplication.clipboard()
    if clipboard:
        clipboard.setText(text)


def get_selection() -> str:
    """
    Записываем выделенный на экране текст в буфер обмена, считываем его оттуда и возвращаем.
    В случае неудачи делаем несколько попыток.

    :return: (str) - Выделенный текст или '' (пустая строка).
    """
    time_delay = C.TIME_DELAY_CTRL_C
    for _ in range(C.MAX_CLIPBOARD_READS):
        text_from_clipboard = get_it_once(time_delay)
        if text_from_clipboard:
            return text_from_clipboard
        logger.info(C.LOGGER_TEXT_NO_IN_CLIPBOARD.format(time_delay=time_delay))
        # Подготовка к следующей итерации
        time_delay += C.TIME_DELAY_CTRL_C

    logger.info(f"{C.LOGGER_TEXT_ERROR_READ_CLIPBOARD}")
    return ""


def get_it_once(time_delay: float) -> str | None:
    """
    Считывает выделенный текст в буфер обмена.

    :param time_delay: (float) - время задержки проверки после нажатия клавиш Ctrl+C (в секундах).

    :return: (str) Текст, считанный из буфера обмена
    """

    clipboard = QApplication.clipboard()
    if clipboard:
        clipboard.clear()
    VK_C = 0x43  # "C"
    controller.press_ctrl(VK_C)
    return get_clipboard_text()


def get_clipboard_text() -> str:
    """
    Возвращаем текст буфера обмена
    :return: (str).
    """
    clipboard = QApplication.clipboard()
    return clipboard.text() if clipboard else ""


# noinspection PyProtectedMember
def get_window() -> gw._pygetwindow_win.Win32Window | None:
    """
    Возвращает активное окно операционной системы.

    :return: Объект окна Win32Window, если активное окно найдено,
             иначе None.
    """
    return gw.getActiveWindow()


def replace_selected_text():
    """Заменяем выделенный текст"""
    VK_V = 0x56  # v
    ll_keyboard.press_ctrl(VK_V, C.TIME_DELAY_CTRL_V)  # Эмуляция Ctrl+v
