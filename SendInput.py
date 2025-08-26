import time
import ctypes

user32 = ctypes.WinDLL("user32", use_last_error=True)

# Константы WinAPI
KEYEVENTF_KEYUP = 0x0002
VK_LWIN = 0x5B
VK_R = 0x52
VK_RETURN = 0x0D


def press_key(vk_code):
    user32.keybd_event(vk_code, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.05)


def set_english_layout():
    # 00000409 — англ. (США). Активируем независимо от текущей раскладки.
    hkl = user32.LoadKeyboardLayoutW("00000409", 0)
    user32.ActivateKeyboardLayout(hkl, 0)


def open_notepad_via_run():
    # Win+R
    user32.keybd_event(VK_LWIN, 0, 0, 0)
    user32.keybd_event(VK_R, 0, 0, 0)
    user32.keybd_event(VK_R, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.2)

    set_english_layout()  # переключаемся на английскую раскладку

    for ch in "notepad":  # вводим текст
        press_key(ord(ch.upper()))

    press_key(VK_RETURN)  # Enter


if __name__ == "__main__":
    open_notepad_via_run()
