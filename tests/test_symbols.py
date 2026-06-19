from SRC.symbols import en_to_ru


def test_layout_mapping_contains_expected_letters_and_punctuation() -> None:
    expected = {
        "q": "й",
        "Q": "Й",
        "f": "а",
        "F": "А",
        "?": ",",
        "/": ".",
        "`": "ё",
    }

    for source, target in expected.items():
        assert en_to_ru[source] == target


def test_layout_mapping_uses_single_character_keys_and_values() -> None:
    for source, target in en_to_ru.items():
        assert len(source) == 1
        assert len(target) == 1


def test_layout_mapping_has_no_empty_values() -> None:
    assert all(en_to_ru.keys())
    assert all(en_to_ru.values())