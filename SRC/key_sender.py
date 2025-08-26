"""
Автоматизация имитация ввода с клавиатуры для Windows (только клавиатура).

Назначение
---------
Модуль отправляет системные события клавиатуры в активное окно:
- "горячие клавиши" через `keybd_event` (надёжно для глобальных сочетаний вроде Win+R);
- ввод текста любой раскладки через `SendInput` с флагом `KEY_EVENT_F_UNICODE`;
- эмуляция нажатий по скан кодам через `SendInput` с флагом `KEY_EVENT_F_SCANCODE`,
  с автоматической установкой `KEY_EVENT_F_EXTENDED_KEY` для "extended"-клавиш.

Совместимость
------------
- Только Windows.
- CPython 3.11/3.12/3.13. В некоторых версиях Python отсутствует
  `wintypes.ULONG_PTR`, поэтому предусмотрен запасной тип (`WPARAM`).

В union нет MOUSE/HARDWARE
---------------------------------
Для корректной работы `SendInput` размер структуры `INPUT` должен совпадать с
системным (40 байт на x64, 28 байт на x86). Мы используем union только с
`KEYBD_INPUT` и добавочным заполнителем (`_pad`), чтобы добиться правильного размера,
не внедряя поддержку мыши и аппаратных сообщений.

Быстрый старт
-------------
пример использования в конце данного модуля

Замечание о потоках
-------------------
Текущая реализация без внутренней блокировки.

Автор: Большаков Л. А.
Лицензия: CC BY Creative Commons Attribution 4.0 International
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import time
from contextlib import contextmanager
from dataclasses import dataclass
from enum import IntEnum, IntFlag
from typing import Iterable, Optional

__all__ = ["VK", "Timings", "KeystrokeAutomator"]
__version__ = "2.0-doc"

# --- Базовые объекты WinAPI ---
user32 = ctypes.WinDLL("user32", use_last_error=True)


# --- Битовые флаги для KEYBD_INPUT.dwFlags при вызове SendInput.
#     Соответствуют WinAPI KEY_EVENT_F_* и комбинируются через |.
#     Нельзя совмещать UNICODE и SCANCODE одновременно.
# noinspection PyPep8Naming
class KEY_EVENT_F(IntFlag):
    EXTENDED_KEY = 0x0001  # «расширенная» клавиша (E0): стрелки, Insert/Delete, ...
    KEYUP = 0x0002  # отпускание клавиши (без флага — нажатие)
    UNICODE = (
        0x0004  # ввод символа по Unicode: wVk=0, wScan=код UTF-16, раскладка не важна.
    )
    SCANCODE = 0x0008  # ввод по скан коду: wVk=0, wScan=скан код; при нужде добавьте EXTENDED_KEY


# --- Константы
INPUT_KEYBOARD = 1  # Константа для SendInput с типом клавиатурного ввода
MAP_VK_VK_TO_VSC = 0  # Режим MapVirtualKeyW: VK -> scan code
ULONG_PTR = getattr(
    wt, "ULONG_PTR", wt.WPARAM
)  # --- Совместимый с разрядностью тип ULONG_PTR ---

# Прототипы функций WinAPI
SendInput = user32.SendInput

# Аргументы уточняются после объявления структуры INPUT
SendInput.argtypes = (wt.UINT, ctypes.POINTER(ctypes.c_byte), ctypes.c_int)
SendInput.restype = wt.UINT

MapVirtualKeyW = user32.MapVirtualKeyW
MapVirtualKeyW.argtypes = (wt.UINT, wt.UINT)
MapVirtualKeyW.restype = wt.UINT


# --- Структуры для SendInput (клавиатура) ---
class KEYBDINPUT(ctypes.Structure):
    """
    Полезная нагрузка для клавиатурного INPUT.

    Поля:
      wVk        — виртуальный код клавиши (0, если используем скан код/UNICODE);
      wScan      — скан код (или Unicode-символ при KEY_EVENT_F.UNICODE);
      dwFlags    — флаги KEY_EVENT_F_*;
      time       — метка времени (0 = система выставит автоматически);
      dwExtraInfo— дополнительная информация (ULONG_PTR).
    """

    _fields_ = (
        ("wVk", wt.WORD),
        ("wScan", wt.WORD),
        ("dwFlags", wt.DWORD),
        ("time", wt.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    )


# Размер union внутри INPUT должен совпадать с системным.
# На x64 это 32 байта, на x86 — 24 байта.
_UNION_BYTES = 32 if ctypes.sizeof(ctypes.c_void_p) == 8 else 24


class KbdOnlyUnion(ctypes.Union):
    """
    Union для структуры INPUT, содержащий только KEYBDINPUT и заполнитель.
    Заполнитель `_pad` гарантирует системный размер union без включения MOUSE/HARDWARE.
    """

    _fields_ = (
        ("ki", KEYBDINPUT),
        ("_pad", ctypes.c_byte * _UNION_BYTES),
    )


class INPUT(ctypes.Structure):
    """
    Обёртка, которую принимает SendInput. Поля фиксированы WinAPI:
      type — тип записи (для клавиатуры = 1);
      u    — union полезной нагрузки (у нас — KbdOnlyUnion).
    """

    _fields_ = (("type", wt.DWORD), ("u", KbdOnlyUnion))


# После определения INPUT можно выставить корректный прототип SendInput
SendInput.argtypes = (wt.UINT, ctypes.POINTER(INPUT), ctypes.c_int)


# --- Перечень виртуальных кодов (не полный) ---
class VK(IntEnum):
    """Подмножество виртуальных кодов клавиш для удобства обращения."""

    SHIFT = 0x10
    CONTROL = 0x11
    MENU = 0x12  # Alt
    L_WIN = 0x5B
    RWIN = 0x5C
    APPS = 0x5D

    RETURN = 0x0D
    ESCAPE = 0x1B
    SPACE = 0x20
    LEFT = 0x25
    UP = 0x26
    RIGHT = 0x27
    DOWN = 0x28
    INSERT = 0x2D
    DELETE = 0x2E
    HOME = 0x24
    END = 0x23
    PRIOR = 0x21  # PgUp
    NEXT = 0x22  # PgDn


# Набор "extended"-клавиш, требующих KEY_EVEN_F.EXTENDED_KEY при вводе скан кодом.
_EXTENDED_VKS = {
    int(VK.L_WIN),
    int(VK.RWIN),
    int(VK.APPS),
    int(VK.RIGHT),
    int(VK.LEFT),
    int(VK.UP),
    int(VK.DOWN),
    int(VK.INSERT),
    int(VK.DELETE),
    int(VK.HOME),
    int(VK.END),
    int(VK.PRIOR),
    int(VK.NEXT),
    0xA5,  # VK_RMENU (Right Alt)
    0xA3,  # VK_RCONTROL
}


@dataclass
class Timings:
    """
    Интервалы ожидания (в секундах) для повышения надёжности ввода:
      press — пауза между "down" и "up" одной клавиши;
      after — пауза после завершения операции;
      combo — пауза между нажатиями внутри сочетания.
    """

    press: float = 0.03
    after: float = 0.03
    combo: float = 0.03


class KeystrokeAutomator:
    """
    Высокоуровневый API для отправки событий клавиатуры.

    Методы:
      key_down(vk) / key_up(vk)       — прямые нажатия через keybd_event;
      tap(vk)                         — короткое нажатие;
      combo(main_vk, modifiers)       — сочетание клавиш (например, Win+R);
      hold(modifiers)                 — контекст-менеджер удержания модификаторов;
      send_unicode(text)              — ввод строки юни кодом (раскладка не важна);
      tap_sc(vk), combo_sc(...)       — ввод по скан кодам через SendInput.

    Важно:
      - Ввод UNICODE и SCANCODE создаёт единый буфер INPUT и отправляет его
        одним вызовом SendInput (как рекомендует MSDN).
      - Для SCANCODE автоматически проставляется EXTENDED-флаг там, где нужно.
    """

    def __init__(self, timings: Optional[Timings] = None):
        self.timings = timings or Timings()

    # -------- keybd_event: базовые операции --------
    @staticmethod
    def key_down(vk: int) -> None:
        """Нажать клавишу с виртуальным кодом `vk` (KeyDown)."""
        user32.keybd_event(int(vk), 0, 0, 0)

    @staticmethod
    def key_up(vk: int) -> None:
        """Отпустить клавишу с виртуальным кодом `vk` (KeyUp)."""
        user32.keybd_event(int(vk), 0, KEY_EVENT_F.KEYUP, 0)

    def tap(self, vk: int) -> None:
        """Коротко нажать клавишу: Down → пауза `press` → Up → пауза `after`."""
        self.key_down(vk)
        time.sleep(self.timings.press)
        self.key_up(vk)
        time.sleep(self.timings.after)

    def combo(self, main_vk: int | VK, modifiers: Iterable[int | VK]) -> None:
        """
        Выполнить сочетание: зажать модификаторы → нажать/отпустить основную →
        отпустить модификаторы в обратном порядке. Паузы — `combo`.
        """
        vk_main = int(main_vk)
        mods = list(
            dict.fromkeys(int(m) for m in modifiers)
        )  # убрать дубли, сохранить порядок
        for m in mods:
            self.key_down(m)
            time.sleep(self.timings.combo)
        self.key_down(vk_main)
        time.sleep(self.timings.combo)
        self.key_up(vk_main)
        time.sleep(self.timings.combo)
        for m in reversed(mods):
            self.key_up(m)
            time.sleep(self.timings.combo)
        time.sleep(self.timings.after)

    @contextmanager
    def hold(self, modifiers: Iterable[int]):
        """
        Контекст удержания модификаторов:
        with kb.hold([VK.CONTROL, VK.SHIFT]):
            kb.tap(ord('S'))
        """
        mods = list(dict.fromkeys(int(m) for m in modifiers))
        try:
            for m in mods:
                self.key_down(m)
                time.sleep(self.timings.combo)
            yield
        finally:
            for m in reversed(mods):
                self.key_up(m)
                time.sleep(self.timings.combo)

    # -------- SendInput: общие вспомогательные --------
    @staticmethod
    def _send_inputs(inputs: list[INPUT]) -> None:
        """
        Отправить массив структур INPUT одним вызовом SendInput.
        Бросает OSError при частичной/нулевой отправке.
        """
        if not inputs:
            return
        arr = (INPUT * len(inputs))(*inputs)  # непрерывный буфер
        sent = SendInput(len(arr), arr, ctypes.sizeof(INPUT))
        if sent != len(arr):
            err = ctypes.get_last_error()
            raise OSError(f"SendInput sent {sent}/{len(arr)} items, GetLastError={err}")

    # -------- UNICODE-ввод --------
    def send_unicode(self, text: str) -> None:
        """
        Ввести текст как последовательность Unicode-событий.
        Не зависит от активной раскладки клавиатуры.
        """
        ins: list[INPUT] = []
        for ch in text:
            code = ord(ch)
            ins.append(
                INPUT(
                    INPUT_KEYBOARD,
                    KbdOnlyUnion(ki=KEYBDINPUT(0, code, KEY_EVENT_F.UNICODE, 0, 0)),
                )
            )
            ins.append(
                INPUT(
                    INPUT_KEYBOARD,
                    KbdOnlyUnion(
                        ki=KEYBDINPUT(
                            0, code, KEY_EVENT_F.UNICODE | KEY_EVENT_F.KEYUP, 0, 0
                        )
                    ),
                )
            )
        self._send_inputs(ins)
        time.sleep(self.timings.after)

    # -------- SCANCODE-ввод --------
    @staticmethod
    def _is_extended_vk(vk: int | VK) -> bool:
        """Проверить, нужна ли клавише `vk` установка флага EXTENDED при SCANCODE-вводе."""
        return int(vk) in _EXTENDED_VKS

    @staticmethod
    def _vk_to_sc(vk: int) -> int:
        """Преобразовать виртуальный код `vk` в скан код через MapVirtualKeyW."""
        sc = MapVirtualKeyW(int(vk), MAP_VK_VK_TO_VSC)
        return int(sc) & 0xFFFF

    def key_down_sc(self, vk: int, extended: Optional[bool] = None) -> INPUT:
        """Сформировать событие KeyDown по скан коду для `vk`."""
        if extended is None:
            extended = self._is_extended_vk(vk)
        sc = self._vk_to_sc(vk)
        flags = KEY_EVENT_F.SCANCODE | (KEY_EVENT_F.EXTENDED_KEY if extended else 0)
        return INPUT(INPUT_KEYBOARD, KbdOnlyUnion(ki=KEYBDINPUT(0, sc, flags, 0, 0)))

    def key_up_sc(self, vk: int, extended: Optional[bool] = None) -> INPUT:
        """Сформировать событие KeyUp по скан коду для `vk`."""
        if extended is None:
            extended = self._is_extended_vk(vk)
        sc = self._vk_to_sc(vk)
        flags = (
            KEY_EVENT_F.SCANCODE
            | KEY_EVENT_F.KEYUP
            | (KEY_EVENT_F.EXTENDED_KEY if extended else 0)
        )
        return INPUT(INPUT_KEYBOARD, KbdOnlyUnion(ki=KEYBDINPUT(0, sc, flags, 0, 0)))

    def tap_sc(self, vk: int, extended: Optional[bool] = None) -> None:
        """Короткое нажатие клавиши `vk` через SCANCODE-ввод."""
        ins = [self.key_down_sc(vk, extended), self.key_up_sc(vk, extended)]
        self._send_inputs(ins)
        time.sleep(self.timings.after)

    def combo_sc(self, main_vk: int, modifiers: Iterable[int]) -> None:
        """
        Сочетание клавиш целиком через SCANCODE-ввод.
        Для некоторых приложений это срабатывает лучше, чем keybd_event.
        """
        mods = list(dict.fromkeys(int(m) for m in modifiers))
        ins: list[INPUT] = []
        for m in mods:
            ins.append(self.key_down_sc(m))
        ins.append(self.key_down_sc(main_vk))
        ins.append(self.key_up_sc(main_vk))
        for m in reversed(mods):
            ins.append(self.key_up_sc(m))
        self._send_inputs(ins)
        time.sleep(self.timings.after)


# --- Пример использования ---
if __name__ == "__main__":
    kb = KeystrokeAutomator(Timings(press=0.02, after=0.20, combo=0.02))
    kb.combo(ord("R"), [VK.L_WIN])  # Win+R
    time.sleep(0.25)
    kb.send_unicode("notepad")
    kb.tap(VK.RETURN)
