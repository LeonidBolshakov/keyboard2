import logging

import pytest

from SRC.try_log import log_exceptions


def test_log_exceptions_suppresses_exception_by_default(caplog) -> None:
    def fail() -> None:
        raise ValueError("boom")

    wrapped = log_exceptions(name="custom failure")(fail)

    with caplog.at_level(logging.ERROR, logger="SRC.try_log"):
        assert wrapped() is None

    assert "custom failure" in caplog.text
    assert "ValueError: boom" in caplog.text


def test_log_exceptions_reraises_when_requested(caplog) -> None:
    def fail() -> None:
        raise RuntimeError("boom")

    wrapped = log_exceptions(name="reraised failure", reraise=True)(fail)

    with caplog.at_level(logging.ERROR, logger="SRC.try_log"):
        with pytest.raises(RuntimeError, match="boom"):
            wrapped()

    assert "reraised failure" in caplog.text


def test_log_exceptions_can_be_used_without_parentheses(caplog) -> None:
    @log_exceptions
    def fail() -> None:
        raise LookupError("boom")

    with caplog.at_level(logging.ERROR, logger="SRC.try_log"):
        assert fail() is None

    assert "test_log_exceptions_can_be_used_without_parentheses" in caplog.text