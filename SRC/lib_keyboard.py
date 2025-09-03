import time, threading
from keyboard import send, release, write

try:
    import pyperclip
except ImportError:
    pyperclip = None


class LibKeyboard:
    def write_text(self, text: str) -> None:
        text_fast = text.replace("\\n", "\n")
        print(text, text_fast.split("\n"))

        def go():
            for m in ("ctrl", "alt", "shift", "windows"):
                try:
                    release(m)
                except:
                    pass
            time.sleep(0.03)
            # Быстрое “набирание”
            write(text_fast, delay=0, restore_state_after=False, exact=True)

        threading.Timer(0.05, go).start()

    def send_key(self, key: str) -> None:
        send(key)
