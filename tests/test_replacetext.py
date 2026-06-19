from SRC.replacetext import ReplaceText


def test_swap_keyboard_register() -> None:
    replacer = ReplaceText()
    cases = [
        ("ghbdtn", "привет"),
        ("F,hf-rflf,hf", "Абра-кадабра"),
        ("руддщ", "hello"),
        ("Ghbdtn? Vbh!", "Привет, Мир!"),
        ("123 +- =", "123 +- ="),
        ("", ""),
    ]

    for source, expected in cases:
        assert replacer.swap_keyboard_register(source) == expected


def test_swap_keyboard_register_keeps_unknown_symbols() -> None:
    replacer = ReplaceText()

    assert replacer.swap_keyboard_register("🙂 123") == "🙂 123"
