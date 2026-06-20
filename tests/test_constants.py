import logging

from src.constants import C


def test_constants_are_read_only() -> None:
    try:
        C.CONSOLE_LOG_LEVEL = "DEBUG"
    except AttributeError as exc:
        assert "Нельзя менять константу CONSOLE_LOG_LEVEL" in str(exc)
    else:
        raise AssertionError("Константы нельзя изменять")


def test_logging_level_names_are_mapped_to_logging_codes() -> None:
    assert C.CONVERT_LOGGING_NAME_TO_CODE["DEBUG"] == logging.DEBUG
    assert C.CONVERT_LOGGING_NAME_TO_CODE["INFO"] == logging.INFO
    assert C.CONVERT_LOGGING_NAME_TO_CODE["WARNING"] == logging.WARNING
    assert C.CONVERT_LOGGING_NAME_TO_CODE["ERROR"] == logging.ERROR
    assert C.CONVERT_LOGGING_NAME_TO_CODE["CRITICAL"] == logging.CRITICAL


def test_default_log_file_path_points_to_keyboard2_log() -> None:
    assert C.FILE_LOG_PATH_DEF.endswith("keyboard2\\logs\\keyboard2.log")
