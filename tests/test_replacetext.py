import pytest

from SRC.replacetext import ReplaceText


@pytest.fixture
def replacer() -> ReplaceText:
    return ReplaceText()


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("ghbdtn", "привет"),
        ("F,hf-rflf,hf", "Абра-кадабра"),
        ("руддщ", "hello"),
        ("Ghbdtn? Vbh!", "Привет, Мир!"),
        ("123 +- =", "123 +- ="),
        ("", ""),
    ],
)
def test_swap_keyboard_register(source: str, expected: str, replacer: ReplaceText) -> None:
    assert replacer.swap_keyboard_register(source) == expected


def test_swap_keyboard_register_keeps_unknown_symbols(replacer: ReplaceText) -> None:
    assert replacer.swap_keyboard_register("🙂 123") == "🙂 123"