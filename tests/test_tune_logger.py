import logging

from SRC.constants import C
from SRC.tune_logger import TuneLogger


class FakeVariables:
    def __init__(self, values: dict[str, object]) -> None:
        self.values = values

    def get_var(self, name: str, default: str = "") -> object:
        return self.values.get(name, default)


def make_logger_with_env(values: dict[str, object]) -> TuneLogger:
    logger = object.__new__(TuneLogger)
    logger.variables = FakeVariables(values)
    return logger


def test_get_log_level_reads_level_from_environment_name() -> None:
    logger = make_logger_with_env({C.CONSOLE_LOG_LEVEL: "WARNING"})

    assert (
        logger._get_log_level(C.CONSOLE_LOG_LEVEL, C.CONSOLE_LOG_LEVEL_DEF)
        == logging.WARNING
    )


def test_get_log_level_is_case_insensitive() -> None:
    logger = make_logger_with_env({C.CONSOLE_LOG_LEVEL: "error"})

    assert (
        logger._get_log_level(C.CONSOLE_LOG_LEVEL, C.CONSOLE_LOG_LEVEL_DEF)
        == logging.ERROR
    )


def test_get_log_level_uses_default_when_variable_is_missing() -> None:
    logger = make_logger_with_env({})

    assert logger._get_log_level(C.CONSOLE_LOG_LEVEL, "INFO") == logging.INFO


def test_get_log_level_falls_back_to_debug_for_unknown_name() -> None:
    logger = make_logger_with_env({C.CONSOLE_LOG_LEVEL: "VERBOSE"})

    assert (
        logger._get_log_level(C.CONSOLE_LOG_LEVEL, C.CONSOLE_LOG_LEVEL_DEF)
        == logging.DEBUG
    )


def test_get_log_level_uses_default_when_value_is_not_string() -> None:
    logger = make_logger_with_env({C.CONSOLE_LOG_LEVEL: 123})

    assert logger._get_log_level(C.CONSOLE_LOG_LEVEL, "CRITICAL") == logging.CRITICAL