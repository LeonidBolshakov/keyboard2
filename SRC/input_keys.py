import time, ctypes
from ctypes import wintypes
from typing import SupportsFloat, SupportsInt, Sequence

user32 = ctypes.WinDLL("user32", use_last_error=True)

# типы и константы
ULONG_PTR = (
    ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong
)
INPUT_KEYBOARD = 1
KEY_EVENT_F_KEYUP = 0x0002
KEY_EVENT_F_UNICODE = 0x0004
VK_RETURN = 0x0D
VK_CONTROL = 0x11


# структуры SendInput
class MOUSE_INPUT(ctypes.Structure):

    _fields_ = (
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    )


class KEYBDINPUT(ctypes.Structure):
    _fields_ = (
        ("wVk", wintypes.WORD),  # Виртуальный код VK. При SCANCODE или UNICODE = 0.
        ("wScan", wintypes.WORD),
        # с KEY_EVENT_F_SCANCODE — скан-код (Set 1).
        # с KEY_EVENT_F_UNICODE — UTF-16 код UTF-16 символа.
        # иначе игнорируется, держите 0.
        ("dwFlags", wintypes.DWORD),
        # KEY_EVENT_F_KEYUP (0x0002) — отпускание; без него — нажатие.
        # KEY_EVENT_F_SCANCODE (0x0008) — брать wScan как скан-код, wVk=0.
        # KEY_EVENT_F_UNICODE (0x0004) — послать Unicode символ, wVk=0.
        # KEY_EVENT_F_EXTENDED_KEY (0x0001) — «расширённые» клавиши с префиксом E0/E1:
        # стрелки, Insert/Delete, Home/End, PgUp/PgDn, разделение на NumPad’е, Right Ctrl/Alt, и др.
        # Ставьте этот флаг вместе с SCANCODE, когда у соответствующей клавиши префикс E0/E1.
        (
            "time",
            wintypes.DWORD,
        ),
        # Метка времени события в мс с момента загрузки системы. Обычно 0
        ("dwExtraInfo", ULONG_PTR),  # Произвольный тег отправителя. По умолчанию 0
    )


class HARDWARE_INPUT(ctypes.Structure):
    _fields_ = (
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    )


class INPUT(ctypes.Structure):
    class _U(ctypes.Union):
        _fields_ = (("mi", MOUSE_INPUT), ("ki", KEYBDINPUT), ("hi", HARDWARE_INPUT))

    _anonymous_ = ("u",)
    _fields_ = (("type", wintypes.DWORD), ("u", _U))


class SendInputKeyboard(object):
    """
    Обёртка над WinAPI SendInput для горячих клавиш и ввода текста.

    Возможности:
      - press_ctrl_and_vk(vk, hold_ms): Ctrl+<vk> детерминировано, с точным удержанием.
      - type_text(s, per_char_delay_ms): посимвольный ввод Unicode (KEY_EVENT_F_UNICODE).
      - press_combo(mods, vk, hold_ms): произвольные сочетания модификаторов с клавишей.

    Платформа:
      Windows, Python 3.x, ctypes. Ввод идёт в foreground-окно.
      Фокус обеспечивает вызывающий код.

    Ограничения:
      - KEY_EVENT_F_UNICODE не комбинируется с модификаторами.
      Для Enter/Tab/Shift+Enter используйте press_combo().
      - Для больших объёмов текста используйте пакетирование символов или буфер обмена и Ctrl+V.

    Исключения:
      OSError — ошибка SendInput/WinAPI. Проверяйте размеры структур и типы.

    Пример:
      ik = SendInputKeyboard()
      ik.press_ctrl_and_vk(0x43)         # Ctrl+C
      ik.press_combo([0x10], 0x0D)       # Shift+Enter (VK_SHIFT, VK_RETURN)
      ik.type_text("Привет", 2)          # по 2 мс между символами
    """

    def _busy_wait_ms(self, ms: SupportsFloat) -> None:
        """
        Точное ожидание ms миллисекунд.
        Использует sleep для грубой части и спин-ожидание для точной доводки.
        """
        ms = float(ms)
        if ms <= 0:
            return
        # грубо уснём, тонко — доспим
        coarse = max(0.0, ms / 1000.0 - 0.002)
        if coarse > 0:
            time.sleep(coarse)
        t_end = time.perf_counter() + (ms / 1000.0 - coarse)
        while time.perf_counter() < t_end:
            pass

    def _clamp_hold_ms(self, ms: SupportsInt) -> int:
        """
        Нормализует пользовательское значение удержания в диапазон [0, 1000] мс.
        Некорректный ввод трактуется как 0.
        """
        if ms is None:
            return 0
        try:
            ms = int(ms)
        except Exception:
            ms = 0
        if ms < 0:
            ms = 0
        if ms > 1000:
            ms = 1000
        return ms

    def press_ctrl_and_vk(self, vk: int, hold_ms: int | float = 0) -> None:
        """
        Отправляет сочетание Ctrl+<vk> через SendInput.

        Параметры:
            vk (int): Виртуальный код клавиши (VK_*).
            hold_ms (int|float): Время удержания целевой клавиши в мс.
                Нормализуется в диапазон 0..1000. 0 = без удержания.

        Поведение:
            - При ms==0 отправляет пакет из четырёх событий: Ctrl↓, Key↓, Key↑, Ctrl↑.
            - При ms>0 отправляет Ctrl↓+Key↓, ждёт ms (гибрид sleep+spin), затем Key↑+Ctrl↑.
            - В finally дублирует отпускания для страховки от «залипания».

        Исключения:
            OSError: ошибка SendInput (например, неверный размер INPUT или блокировка ввода).

        Примечания:
            Целевое окно должно быть активным. Используйте bring_word_foreground() для Word.
        """

        ms = self._clamp_hold_ms(hold_ms)
        try:
            if ms == 0:
                self._send(
                    [
                        self._vk(VK_CONTROL, 0),
                        self._vk(vk, 0),
                        self._vk(vk, KEY_EVENT_F_KEYUP),
                        self._vk(VK_CONTROL, KEY_EVENT_F_KEYUP),
                    ]
                )
            else:
                self._send([self._vk(VK_CONTROL, 0), self._vk(vk, 0)])
                self._busy_wait_ms(ms)
                self._send(
                    [
                        self._vk(vk, KEY_EVENT_F_KEYUP),
                        self._vk(VK_CONTROL, KEY_EVENT_F_KEYUP),
                    ]
                )
        finally:
            # страховка от залипания
            try:
                self._send(
                    [
                        self._vk(vk, KEY_EVENT_F_KEYUP),
                        self._vk(VK_CONTROL, KEY_EVENT_F_KEYUP),
                    ]
                )
            except OSError:
                pass

    def _send(self, seq: Sequence[INPUT]) -> None:
        """
        Вспомогательная отправка массива INPUT через SendInput с проверкой результата.

        Параметры:
            seq (list[INPUT]): Список подготовленных событий клавиатуры.

        Исключения:
            OSError: если SendInput вернул число < len(seq).
        """
        arr = (INPUT * len(seq))(*seq)
        sent = user32.SendInput(len(seq), arr, ctypes.sizeof(INPUT))
        if sent != len(seq):
            raise ctypes.WinError(ctypes.get_last_error())

    def _vk(self, vk: int, flags: int = 0) -> INPUT:
        """
        Формирует INPUT для клавиатурного события по виртуальному коду (VK).

        Параметры:
            vk: код VK целевой клавиши (напр. VK_CONTROL, VK_V).
            flags: маска KEY_EVENT_F_* (0 — нажатие; KEY_EVENT_F_KEYUP — отпускание).

        Возвращает:
            INPUT с type=INPUT_KEYBOARD и KEYBDINPUT(wVk=vk, wScan=0, dwFlags=flags, time=0, dwExtraInfo=0).

        Примечание:
            Для scancode/UNICODE нужны отдельные конструкторы.
        """
        i = INPUT()
        i.type = INPUT_KEYBOARD
        i.ki = KEYBDINPUT(vk, 0, flags, 0, 0)
        return i

    def _uni(self, code_unit: int, keyup: bool = False) -> INPUT:
        """
        Построить INPUT для одной кодовая единица (UTF-16) (KEY_EVENT_F_UNICODE).
        Примечание: если исходные данные в UTF-8, сначала декодируйте в str
        и используйте _send_unicode_char/type_text. Непосредственно UTF-8
        в SendInput не передаётся..

        Параметры:
          code_unit: кодовая единица (UTF-16) (в т. ч. суррогаты).
          keyup: True — отпускание, False — нажатие.

        Поведение:
          Формирует KEYBDINPUT с wVk=0, wScan=code_unit, dwFlags=KEY_EVENT_F_UNICODE | [KEYUP].

        Возврат:
          Готовая структура INPUT для SendInput.
        """
        e = INPUT()
        e.type = 1  # INPUT_KEYBOARD
        e.ki = KEYBDINPUT(
            0,
            code_unit,
            KEY_EVENT_F_UNICODE | (KEY_EVENT_F_KEYUP if keyup else 0),
            0,
            0,
        )
        return e

    def _send_unicode_char(self, ch: str) -> None:
        """
        Отправить один символ Unicode в активное окно.

        Правила:
          - '\\n' отправляется как VK_RETURN (некоторые элемент управления не принимают UNICODE-Enter).
          - Символы ≤ U+FFFF — одна кодовая единица (UTF-16) (нажатие+отпускание).
          - Символы > U+FFFF — суррогатная пара: high↓, low↓, low↑, high↑.

        Примечание:
          Модификаторы (Ctrl/Alt/Shift) тут не участвуют. Для сочетаний используйте press_combo().
        """
        cp = ord(ch)

        if ch == "\n":
            self._send([self._vk(VK_RETURN, 0), self._vk(VK_RETURN, KEY_EVENT_F_KEYUP)])
            return

        if cp <= 0xFFFF:
            self._send([self._uni(cp, False), self._uni(cp, True)])
            return

        cp -= 0x10000
        high = 0xD800 + ((cp >> 10) & 0x3FF)
        low = 0xDC00 + (cp & 0x3FF)
        self._send(
            [
                self._uni(high, False),
                self._uni(low, False),
                self._uni(low, True),
                self._uni(high, True),
            ]
        )

    def type_text(self, s: str, per_char_delay_ms: int = 0) -> None:
        """
        Посимвольно напечатать строку Unicode.

        Параметры:
          s: текст
          per_char_delay_ms: задержка между символами в мс (0 — без пауз).

        Замечания:
          Для коротких строк (≤200 символов) посимвольный ввод достаточен.
          Для длинных строк лучше пакетировать события или вставлять через буфер обмена.
        """
        delay = max(0, int(per_char_delay_ms))
        for ch in s:
            self._send_unicode_char(ch)
            if delay:
                self._busy_wait_ms(delay)

    def press_combo(self, mods: list[int], vk: int, hold_ms: int = 0) -> None:
        """
        Отправить сочетание модификаторов с клавишей: mods + vk.

        Параметры:
          mods: список VK-кодов модификаторов (напр. [VK_SHIFT, VK_CONTROL]).
          vk: VK целевой клавиши.
          hold_ms: удержание целевой клавиши в мс (0 — без удержания).

        Порядок событий:
          1) Все модификаторы ↓ слева направо, затем vk ↓.
          2) При hold_ms>0 — точное ожидание.
          3) vk ↑, затем модификаторы ↑ в обратном порядке.

        Пример:
          press_combo([VK_SHIFT], VK_RETURN)  # Shift+Enter
        """
        downs = [self._vk(m, 0) for m in mods] + [self._vk(vk, 0)]
        ups = [self._vk(vk, KEY_EVENT_F_KEYUP)] + [
            self._vk(m, KEY_EVENT_F_KEYUP) for m in reversed(mods)
        ]
        if hold_ms <= 0:
            self._send(downs + ups)
        else:
            self._send(downs)
            self._busy_wait_ms(hold_ms)
            self._send(ups)
