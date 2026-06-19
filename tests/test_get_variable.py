import os

from SRC.get_variable import Variables


def test_get_var_returns_environment_value() -> None:
    name = "KEYBOARD2_TEST_VALUE"
    old_value = os.environ.get(name)
    os.environ[name] = "from-env"
    try:
        assert Variables().get_var(name, "default") == "from-env"
    finally:
        if old_value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = old_value


def test_get_var_returns_default_for_missing_value() -> None:
    name = "KEYBOARD2_TEST_MISSING_VALUE"
    old_value = os.environ.pop(name, None)
    try:
        assert Variables().get_var(name, "default") == "default"
    finally:
        if old_value is not None:
            os.environ[name] = old_value


def test_get_var_rejects_non_string_name() -> None:
    try:
        Variables().get_var(123, "default")  # type: ignore[arg-type]
    except TypeError as exc:
        assert "Первый параметр 123" in str(exc)
    else:
        raise AssertionError("get_var must reject non-string variable names")


def test_get_var_rejects_non_string_default() -> None:
    try:
        Variables().get_var("KEYBOARD2_TEST_VALUE", 123)  # type: ignore[arg-type]
    except TypeError as exc:
        assert "Второй параметр 123" in str(exc)
    else:
        raise AssertionError("get_var must reject non-string defaults")