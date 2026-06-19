from SRC.get_variable import Variables


def test_get_var_returns_environment_value(monkeypatch) -> None:
    monkeypatch.setenv("KEYBOARD2_TEST_VALUE", "from-env")

    assert Variables().get_var("KEYBOARD2_TEST_VALUE", "default") == "from-env"


def test_get_var_returns_default_for_missing_value(monkeypatch) -> None:
    monkeypatch.delenv("KEYBOARD2_TEST_MISSING_VALUE", raising=False)

    assert Variables().get_var("KEYBOARD2_TEST_MISSING_VALUE", "default") == "default"


def test_get_var_rejects_non_string_name() -> None:
    try:
        Variables().get_var(123, "default")  # type: ignore[arg-type]
    except TypeError as exc:
        assert "Первый параметр 123" in str(exc)
    else:
        raise AssertionError("Имя переменной окружения должно быть строкой")


def test_get_var_rejects_non_string_default() -> None:
    try:
        Variables().get_var("KEYBOARD2_TEST_VALUE", 123)  # type: ignore[arg-type]
    except TypeError as exc:
        assert "Второй параметр 123" in str(exc)
    else:
        raise AssertionError("Значение по умолчанию должно быть строкой")
