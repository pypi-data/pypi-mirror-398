"""
Реализация паддинга PKCS7
"""

from ..exceptions import CryptoOperationError


class PKCS7Padding:
    """Реализация паддинга по стандарту PKCS7.

    Атрибуты:
        BLOCK_SIZE (int): Размер блока для паддинга (16 байт).
    """

    BLOCK_SIZE = 16

    @staticmethod
    def constant_time_compare(a: bytes, b: bytes) -> bool:
        """
        Сравнение с постоянным временем для защиты от timing attacks.

        Args:
            a (bytes): Первая байтовая последовательность.
            b (bytes): Вторая байтовая последовательность.

        Returns:
            bool: True если последовательности равны, иначе False.
        """
        if len(a) != len(b):
            return False

        result = 0
        for x, y in zip(a, b):
            result |= x ^ y
        return result == 0

    @classmethod
    def pad(cls, data: bytes) -> bytes:
        """
        Добавляет паддинг PKCS7 к данным.

        Args:
            data (bytes): Исходные данные.

        Returns:
            bytes: Данные с добавленным паддингом.
        """
        if len(data) % cls.BLOCK_SIZE == 0:
            pad_len = cls.BLOCK_SIZE
        else:
            pad_len = cls.BLOCK_SIZE - (len(data) % cls.BLOCK_SIZE)
        return data + bytes([pad_len] * pad_len)

    @classmethod
    def unpad(cls, data: bytes) -> bytes:
        """
        Удаляет паддинг PKCS7 из данных.

        Args:
            data (bytes): Данные с паддингом.

        Returns:
            bytes: Данные без паддинга.

        Raises:
            CryptoOperationError: Если паддинг некорректен.
        """
        if not data:
            return data

        pad_len = data[-1]

        # Проверка корректности дополнения
        if pad_len > cls.BLOCK_SIZE or pad_len == 0:
            raise CryptoOperationError("Некорректное дополнение PKCS7")

        if pad_len > len(data):
            raise CryptoOperationError("Некорректная длина паддинга")

        expected_padding = bytes([pad_len] * pad_len)
        actual_padding = data[-pad_len:]

        if not cls.constant_time_compare(expected_padding, actual_padding):
            raise CryptoOperationError("Некорректное дополнение PKCS7")

        return data[:-pad_len]