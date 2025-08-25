"""Класс для замены символов, находящихся на одной клавише"""

from symbols import en_to_ru


class ReplaceText:
    def __init__(self):
        # Обратный словарь (русский -> английский)
        self.ru_to_en = {v: k for k, v in en_to_ru.items()}

    def swap_keyboard_register(self, text_input: str) -> str:
        """
        Обрабатывается каждый символ строки.
        Если символ на русском регистре клавиши, то заменяет его на символ английского регистра клавиши,
        а если на английском регистре, то на русский
        :param text_input: (str) - Входной текст.
        :return: Текст с заменёнными символами.
        """
        text_output = []
        for symbol in text_input:
            if symbol in en_to_ru:  # Если символ на английском регистре
                text_output.append(
                    en_to_ru[symbol]
                )  # заменяем его на символ в русском регистре на той же клавише
            elif symbol in self.ru_to_en:  # Если символ на русском регистре
                text_output.append(
                    self.ru_to_en[symbol]
                )  # заменяем его на символ в английском регистре на той же клавише
            else:
                text_output.append(
                    symbol
                )  # Если символ вне регистров, оставляем его без изменения

        return "".join(text_output)