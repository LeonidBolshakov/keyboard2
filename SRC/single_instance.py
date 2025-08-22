from PyQt6 import QtCore


class SingleInstance:
    def __init__(self, key="__hotkey_singleton__"):
        self.mem = QtCore.QSharedMemory(key)

    def already_running(self) -> bool:
        """
        True, если сегмент памяти с ключом уже существует (другой процесс запущен).
        Подключается к сегменту только для проверки и сразу отцепляется.
        """
        if self.mem.attach():  # сегмент есть → кто-то уже создал
            self.mem.detach()  # мы не пользуемся им — просто проверяли
            return True
        return False

    def claim_ownership(self) -> bool:
        """
        Пытается создать сегмент (размер 1 байт). Возвращает True,
        если создание удалось и теперь этот процесс — «владелец» ключа.
        """
        return self.mem.create(1)
