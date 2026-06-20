from src.replacetext import ReplaceText
from src.symbols import en_to_ru


def test_swap_keyboard_register_common_phrases() -> None:
    replacer = ReplaceText()
    cases = [
        ("ghbdtn", "привет"),
        ("F,hf-rflf,hf", "Абра-кадабра"),
        ("руддщ", "hello"),
        ("Ghbdtn? Vbh!", "Привет, Мир!"),
    ]

    for source, expected in cases:
        assert replacer.swap_keyboard_register(source) == expected


def test_swap_keyboard_register_keeps_text_outside_layout() -> None:
    replacer = ReplaceText()

    assert replacer.swap_keyboard_register("🙂 123 +- =") == "🙂 123 +- ="
    assert replacer.swap_keyboard_register("") == ""


def test_swap_keyboard_register_converts_every_english_mapping() -> None:
    replacer = ReplaceText()
    source = "".join(en_to_ru)
    expected = "".join(en_to_ru.values())

    assert replacer.swap_keyboard_register(source) == expected


def test_converts_non_ambiguous_russian_symbols_back() -> None:
    replacer = ReplaceText()
    reverse_mapping = {
        value: key for key, value in en_to_ru.items() if value not in en_to_ru
    }
    source = "".join(reverse_mapping)
    expected = "".join(reverse_mapping.values())

    assert replacer.swap_keyboard_register(source) == expected


def test_swap_keyboard_register_is_reversible_for_regular_letters() -> None:
    replacer = ReplaceText()
    text = "Привет, keyboard"

    assert (
        replacer.swap_keyboard_register(replacer.swap_keyboard_register(text)) == text
    )
