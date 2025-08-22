# ---- Точка входа
import sys
from logging import getLogger

logger = getLogger(__name__)

from SRC.tunelogger import TuneLogger
from SRC.app import main_app
from SRC.constants import C


def main():
    try:
        tune_logger = TuneLogger()
        tune_logger.setup_logging()
    except Exception as e:
        print(C.TEXT_ERROR_TUNE_LOGGER.format(e=e))
    try:
        app = main_app()
    except SystemExit as e:
        sys.exit(int(e.code) if hasattr(e, "code") else 0)
    except Exception as e:
        logger.exception(C.TEXT_ERROR_TUNE_LOGGER.format(e=e))
        sys.exit(1)
    sys.exit(app.run())


if __name__ == "__main__":
    main()
