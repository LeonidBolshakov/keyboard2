import os
from logging import getLogger

logger = getLogger(__name__)

from dotenv import load_dotenv

load_dotenv()

from constants import C


class Variables:
    def get_var(self, name: str, default: str) -> str:
        if not isinstance(name, str):
            logger.error(C.TEXT_ERROR_GET_VAR_1.format(name=name))
            raise TypeError(C.TEXT_ERROR_GET_VAR_1.format(name=name))

        if not isinstance(default, str):
            logger.error(C.TEXT_ERROR_GET_VAR_2.format(default=default))
            raise TypeError(C.TEXT_ERROR_GET_VAR_2.format(default=default))

        return os.getenv(name, default)
