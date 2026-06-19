from SRC.windows_hotkeys import HI_WORD, LO_WORD


def test_lo_word_returns_low_16_bits() -> None:
    assert LO_WORD(0x12345678) == 0x5678
    assert LO_WORD(0xFFFF0001) == 0x0001
    assert LO_WORD(0x0000FFFF) == 0xFFFF


def test_hi_word_returns_high_16_bits() -> None:
    assert HI_WORD(0x12345678) == 0x1234
    assert HI_WORD(0xFFFF0001) == 0xFFFF
    assert HI_WORD(0x0000FFFF) == 0x0000


def test_lo_word_and_hi_word_split_hotkey_lparam() -> None:
    modifiers = 0x4002
    virtual_key = 0x0073
    lparam = (virtual_key << 16) | modifiers

    assert LO_WORD(lparam) == modifiers
    assert HI_WORD(lparam) == virtual_key