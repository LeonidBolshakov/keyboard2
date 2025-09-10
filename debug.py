"""
Назначение
Скрипт шлёт хоткеи Ctrl+VK в активное окно Word через SendInput. Делает это детерминированно и с минимальными паузами.
Встроена автоподстройка hold_ms по изменению номера буфера обмена.

Требования
Windows, Python 3.x, ctypes. Целевое окно Microsoft Word должно быть на переднем плане. Класс окна: OpusApp.

Публичное API
- press_ctrl_and_vk(vk: int, hold_ms=0): отправить Ctrl+<vk>. Удержание в мс, нормализуется 0..1000.
  Защита от «залипания» в finally.
- autotune_hold_ms_for_copy(candidates=(...), settle_ms=25): подобрать минимальный hold_ms
  по росту GetClipboardSequenceNumber().
- bring_word_foreground(): активирует Word через FindWindowW/ShowWindow/SetForegroundWindow.

Внутренние детали
Структуры MOUSE_INPUT, KEYBDINPUT, HARDWAREINPUT, INPUT соответствуют WinAPI. Размер INPUT корректен;
ULONG_PTR зависит от разрядности. _vk() строит INPUT,
 _send() вызывает SendInput и проверяет результат. _busy_wait_ms() — гибрид sleep+spin. _clamp_hold_ms() валидирует вход.

Ограничения и поведение
Ввод идёт в foreground-окно. Для хоткеев используем VK. Для OEM-клавиш при необходимости — KEYEVENTF_SCANCODE.
Большие hold_ms грузят CPU; для >3–5 мс — гибридное ожидание.

Пример использования
bring_word_foreground()
ms = autotune_hold_ms_for_copy()
press_ctrl_and_vk(VK_C, ms)
press_ctrl_and_vk(VK_V, ms)
"""

import time, ctypes
from ctypes import wintypes, c_size_t, c_void_p
from typing import Iterable, SupportsFloat, SupportsInt, Sequence


user32 = ctypes.WinDLL("user32", use_last_error=True)

# типы и константы
ULONG_PTR = (
    ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong
)
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
VK_CONTROL, VK_C, VK_V = 0x11, 0x43, 0x56
SW_RESTORE = 9

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalFree.restype = wintypes.HGLOBAL
kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalUnlock.restype = wintypes.BOOL
kernel32.GlobalSize.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalSize.restype = ctypes.c_size_t

user32.OpenClipboard.argtypes = [wintypes.HWND]
user32.OpenClipboard.restype = wintypes.BOOL
user32.CloseClipboard.restype = wintypes.BOOL
user32.EmptyClipboard.restype = wintypes.BOOL
user32.IsClipboardFormatAvailable.argtypes = [wintypes.UINT]
user32.IsClipboardFormatAvailable.restype = wintypes.BOOL
user32.GetClipboardData.argtypes = [wintypes.UINT]
user32.GetClipboardData.restype = wintypes.HANDLE
user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
user32.SetClipboardData.restype = wintypes.HANDLE

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002
GMEM_ZEROINIT = 0x0040


# структуры SendInput
class MOUSEINPUT(ctypes.Structure):
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
        # с KEYEVENTF_SCANCODE — скан-код (Set 1).
        # с KEY_EVENT_F_UNICODE — UTF-16 код UTF-16 символа.
        # иначе игнорируется, держите 0.
        ("dwFlags", wintypes.DWORD),
        # KEYEVENTF_KEYUP (0x0002) — отпускание; без него — нажатие.
        # KEYEVENTF_SCANCODE (0x0008) — брать wScan как скан-код, wVk=0.
        # KEY_EVENT_F_UNICODE (0x0004) — послать Unicode символ, wVk=0.
        # KEYEVENTF_EXTENDEDKEY (0x0001) — «расширённые» клавиши с префиксом E0/E1:
        # стрелки, Insert/Delete, Home/End, PgUp/PgDn, разделение на NumPad’е, Right Ctrl/Alt, и др.
        # Ставьте этот флаг вместе с SCANCODE, когда у соответствующей клавиши префикс E0/E1.
        (
            "time",
            wintypes.DWORD,
        ),
        # Метка времени события в мс с момента загрузки системы. Обычно 0
        ("dwExtraInfo", ULONG_PTR),  # Произвольный тег отправителя. По умолчанию 0
    )


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = (
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    )


class INPUT(ctypes.Structure):
    class _U(ctypes.Union):
        _fields_ = (("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT))

    _anonymous_ = ("u",)
    _fields_ = (("type", wintypes.DWORD), ("u", _U))


user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
user32.SendInput.restype = wintypes.UINT
user32.GetClipboardSequenceNumber.restype = wintypes.DWORD


def _vk(vk: int, flags: int = 0) -> None:
    """
    Формирует INPUT для клавиатурного события по виртуальному коду (VK).

    Параметры:
        vk: код VK целевой клавиши (напр. VK_CONTROL, VK_V).
        flags: маска KEYEVENTF_* (0 — нажатие; KEYEVENTF_KEYUP — отпускание).

    Возвращает:
        INPUT с type=INPUT_KEYBOARD и KEYBDINPUT(wVk=vk, wScan=0, dwFlags=flags, time=0, dwExtraInfo=0).

    Примечание:
        Для scancode/UNICODE нужны отдельные конструкторы.
    """
    i = INPUT()
    i.type = INPUT_KEYBOARD
    i.ki = KEYBDINPUT(vk, 0, flags, 0, 0)
    return i


def _send(seq: Iterable[INPUT]) -> None:
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


def bring_word_foreground() -> None:
    """
    Делает окно Microsoft Word активным.

    Действия:
        - Ищет главное окно Word по классу 'OpusApp'.
        - Вызывает ShowWindow(SW_RESTORE) и SetForegroundWindow.
        - Даёт ~10 мс на фокус.

    Возврат:
        None. Если окно не найдено — просто ничего не делает.
    """
    hwnd = user32.FindWindowW("OpusApp", None)
    if hwnd:
        user32.ShowWindow(hwnd, SW_RESTORE)
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.01)


def _busy_wait_ms(ms: SupportsFloat) -> None:
    """
    Точное ожидание ms миллисекунд.
    Использует sleep для грубой части и спин-ожидание для точной доводки.
    """
    ms = float(ms)
    if ms <= 0:
        return
    # грубо уснём, тонко — доспиним
    coarse = max(0.0, ms / 1000.0 - 0.002)
    if coarse > 0:
        time.sleep(coarse)
    t_end = time.perf_counter() + (ms / 1000.0 - coarse)
    while time.perf_counter() < t_end:
        pass


def _clamp_hold_ms(ms: SupportsInt) -> int:
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


def press_ctrl_and_vk(vk: int, hold_ms: int | float = 0) -> None:
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

    ms = _clamp_hold_ms(hold_ms)
    try:
        if ms == 0:
            _send(
                [
                    _vk(VK_CONTROL, 0),
                    _vk(vk, 0),
                    _vk(vk, KEYEVENTF_KEYUP),
                    _vk(VK_CONTROL, KEYEVENTF_KEYUP),
                ]
            )
        else:
            _send([_vk(VK_CONTROL, 0), _vk(vk, 0)])
            _busy_wait_ms(ms)
            _send([_vk(vk, KEYEVENTF_KEYUP), _vk(VK_CONTROL, KEYEVENTF_KEYUP)])
    finally:
        # страховка от залипания
        try:
            _send([_vk(vk, KEYEVENTF_KEYUP), _vk(VK_CONTROL, KEYEVENTF_KEYUP)])
        except OSError:
            pass


def autotune_hold_ms_for_copy(
    candidates: Sequence[int] = (0, 1, 2, 3, 5, 10, 20, 30, 50, 80, 120, 150, 200),
    settle_ms: int = 25,
) -> int:
    """
    Подбирает минимальный hold_ms для надёжного Ctrl+C в Word.

    Алгоритм:
        1) Активирует окно Word.
        2) Для каждого ms из candidates:
           - Запоминает GetClipboardSequenceNumber().
           - Отправляет Ctrl+C с данным ms.
           - Ждёт settle_ms мс.
           - Если номер буфера обмена вырос — возвращает ms.
        3) Если ни один ms не сработал — возвращает последний из candidates.

    Параметры:
        candidates (iterable[int]): Проверяемые значения удержания в мс.
        settle_ms (int): Время на обработку копирования перед проверкой.

    Возврат:
        int: подобранный hold_ms.
    """
    for ms in candidates:
        if copy_succeeded_strict(lambda: press_ctrl_and_vk(VK_C, hold_ms=ms)):
            return ms
    return candidates[-1]


def _set_clip_text(s: str) -> None:
    # открыть с ретраями
    for _ in range(5):
        if user32.OpenClipboard(None):
            break
        time.sleep(0.01)
    else:
        raise OSError("OpenClipboard failed")

    try:
        if not user32.EmptyClipboard():
            raise ctypes.WinError(ctypes.get_last_error())

        nbytes = (len(s) + 1) * ctypes.sizeof(ctypes.c_wchar)
        hmem = kernel32.GlobalAlloc(GMEM_MOVEABLE | GMEM_ZEROINIT, nbytes)
        if not hmem:
            raise ctypes.WinError(ctypes.get_last_error())

        p = kernel32.GlobalLock(hmem)
        if not p:
            err = ctypes.get_last_error()
            kernel32.GlobalFree(hmem)
            raise ctypes.WinError(err)
        try:
            buf = ctypes.create_unicode_buffer(s)
            ctypes.memmove(p, ctypes.addressof(buf), nbytes)
        finally:
            kernel32.GlobalUnlock(hmem)

        if not user32.SetClipboardData(CF_UNICODETEXT, hmem):
            err = ctypes.get_last_error()
            kernel32.GlobalFree(hmem)  # владение не перешло системе
            raise ctypes.WinError(err)
        # успех: память теперь владеет ОС, не трогать
    finally:
        user32.CloseClipboard()


def _get_clip_text() -> str | None:
    if not user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
        return None
    if not user32.OpenClipboard(None):
        return None
    try:
        h = user32.GetClipboardData(CF_UNICODETEXT)
        if not h:
            return None
        kernel32.GlobalLock.restype = ctypes.c_void_p
        p = kernel32.GlobalLock(h)
        try:
            if not p:
                return None
            return ctypes.wstring_at(p)
        finally:
            kernel32.GlobalUnlock(h)
    finally:
        user32.CloseClipboard()


def copy_succeeded_strict(press_copy_fn, timeout=0.25) -> bool:
    """press_copy_fn() должен отправить Ctrl+C в активное окно."""
    sentinel = f"__SENTINEL__{time.perf_counter_ns()}__"
    if not _set_clip_text_retry(sentinel):
        return False
    before = user32.GetClipboardSequenceNumber()
    press_copy_fn()
    deadline = time.perf_counter() + timeout
    while time.perf_counter() < deadline:
        if user32.GetClipboardSequenceNumber() != before:
            txt = _get_clip_text()
            return bool(txt) and txt != sentinel
        time.sleep(0.003)
    return False


def _set_clip_text_retry(s: str, tries=5, delay=0.01):
    for _ in range(tries):
        try:
            _set_clip_text(s)
            return True
        except OSError:
            time.sleep(delay)
    return False


if __name__ == "__main__":
    bring_word_foreground()
    ms_ = autotune_hold_ms_for_copy()  # подберёт 0..30 мс
    press_ctrl_and_vk(VK_C, ms_)  # копия
    press_ctrl_and_vk(VK_V, ms_)  # вставка
    print(ms_)

# CF_UNICODETEXT = 13
#
#
# def copy_succeeded_text(before_seq, timeout=0.15):
#     import time, ctypes
#
#     user32 = ctypes.WinDLL("user32", use_last_error=True)
#
#     deadline = time.perf_counter() + timeout
#     while time.perf_counter() < deadline:
#         if user32.GetClipboardSequenceNumber() != before_seq:
#             # изменился — проверим, есть ли текст
#             if user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
#                 return True
#             # формат не тот — возможно, не текст: решайте по задаче
#             return False
#         time.sleep(0.005)
#     return False
#
#
# before = user32.GetClipboardSequenceNumber()
# hold_ms= 10
# press_ctrl_and_vk(VK_C, hold_ms=hold_ms)
# ok = copy_succeeded_text(before)
