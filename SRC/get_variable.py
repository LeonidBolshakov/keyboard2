"""
Модуль get_variable.py

Назначение
---------
Загрузка переменных окружения и предоставление безопасного доступа к ним
с проверкой типов аргументов. Использует библиотеку python-dotenv для
чтения переменных из файла .env.

Состав
------
- Класс `Variables` с методом `get_var()`, который извлекает переменную
  окружения по имени или возвращает значение по умолчанию.
- Проверка типов аргументов и запись ошибок в лог при неправильном использовании.
"""

import os
from logging import getLogger

logger = getLogger(__name__)

from dotenv import load_dotenv

from SRC.constants import C


class Variables:
    """Класс для получения переменных окружения.

    Методы
    ------
    get_var(name: str, default: str) -> str
        Возвращает значение переменной окружения `name`, если она определена,
        иначе возвращает `default`. Если аргументы переданы не как строки,
        возбуждает TypeError и пишет сообщение об ошибке в лог.
    """

    def __init__(self):
        # Загружаем переменные окружения из файла .env (если он существует)
        load_dotenv()

    def get_var(self, name: str, default: str = "") -> str:
        if not isinstance(name, str):
            logger.error(C.TEXT_ERROR_GET_VAR_1.format(name=name))
            raise TypeError(C.TEXT_ERROR_GET_VAR_1.format(name=name))

        if not isinstance(default, str):
            logger.error(C.TEXT_ERROR_GET_VAR_2.format(default=default))
            raise TypeError(C.TEXT_ERROR_GET_VAR_2.format(default=default))

        return os.getenv(name, default)
