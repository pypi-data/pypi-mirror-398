import os
import sys
from pathlib import Path

from Crypto.Cipher import AES

from ..exceptions import AuthenticationError, CryptoOperationError
from ..csprng import generate_random_bytes


class GCMMode:
    """
    Реализация режима GCM (Galois/Counter Mode) для аутентифицированного шифрования.

    Атрибуты:
        NONCE_SIZE (int): Размер nonce (12 байт).
        TAG_SIZE (int): Размер аутентификационного тега (16 байт).
        BLOCK_SIZE (int): Размер блока AES в байтах (16 байт).
        GF_REDUCTION (int): Константа для редукции в поле Галуа.
    """

    NONCE_SIZE = 12  # 96 bits (recommended)
    TAG_SIZE = 16  # 128 bits
    BLOCK_SIZE = 16  # 128 bits

    GF_REDUCTION = 0xE1 << 120

    def __init__(self, key: bytes, nonce: bytes = None):
        """
        Инициализация режима GCM с ключом и опциональным nonce.

        Args:
            key (bytes): Ключ шифрования (16, 24 или 32 байта).
            nonce (bytes): Nonce. Если None, генерируется случайно.

        Raises:
            ValueError: Если размер ключа или nonce некорректен.
        """
        if len(key) not in (16, 24, 32):
            raise ValueError(f"Неверный размер ключа: {len(key)} байт. Должен быть 16, 24, или 32.")

        self.key = key
        self.cipher = AES.new(key, AES.MODE_ECB)

        self.nonce = nonce if nonce else generate_random_bytes(self.NONCE_SIZE)

        if len(self.nonce) != self.NONCE_SIZE:
            raise ValueError(f"Nonce должен быть {self.NONCE_SIZE} байт, получено {len(self.nonce)}")

        self._H = self._bytes_to_int(
            self.cipher.encrypt(bytes(self.BLOCK_SIZE))
        )

    @staticmethod
    def _bytes_to_int(b: bytes) -> int:
        """
        Преобразование байтов в целое число.

        Args:
            b (bytes): Байтовая последовательность.

        Returns:
            int: Целое число.
        """
        return int.from_bytes(b, 'big')

    @staticmethod
    def _int_to_bytes(n: int, length: int = 16) -> bytes:
        """
        Преобразование целого числа в байты.

        Args:
            n (int): Целое число.
            length (int): Длина выходной последовательности.

        Returns:
            bytes: Байтовая последовательность.
        """
        return n.to_bytes(length, 'big')

    def _gf_mult(self, x: int, y: int) -> int:
        """
        Умножение в поле Галуа GF(2^128).

        Args:
            x (int): Первый множитель.
            y (int): Второй множитель.

        Returns:
            int: Результат умножения.
        """
        z = 0
        v = y

        for i in range(127, -1, -1):
            if (x >> i) & 1:
                z ^= v

            if v & 1:
                v = (v >> 1) ^ self.GF_REDUCTION
            else:
                v >>= 1

        return z

    def _ghash(self, aad: bytes, ciphertext: bytes) -> bytes:
        """
        Вычисление GHASH для аутентификации.

        Args:
            aad (bytes): Дополнительные аутентифицированные данные.
            ciphertext (bytes): Шифртекст.

        Returns:
            bytes: Результат GHASH.
        """
        aad_padded = aad + bytes((self.BLOCK_SIZE - len(aad) % self.BLOCK_SIZE) % self.BLOCK_SIZE)

        ct_padded = ciphertext + bytes((self.BLOCK_SIZE - len(ciphertext) % self.BLOCK_SIZE) % self.BLOCK_SIZE)

        len_block = (len(aad) * 8).to_bytes(8, 'big') + (len(ciphertext) * 8).to_bytes(8, 'big')

        data = aad_padded + ct_padded + len_block

        y = 0
        for i in range(0, len(data), self.BLOCK_SIZE):
            block = self._bytes_to_int(data[i:i + self.BLOCK_SIZE])
            y = self._gf_mult(y ^ block, self._H)

        return self._int_to_bytes(y)

    def _inc32(self, counter: bytes) -> bytes:
        """
        Инкрементирование последних 32 бит счетчика.

        Args:
            counter (bytes): Текущее значение счетчика.

        Returns:
            bytes: Увеличенное значение счетчика.
        """
        nonce_part = counter[:12]
        counter_val = int.from_bytes(counter[12:], 'big')
        counter_val = (counter_val + 1) & 0xFFFFFFFF
        return nonce_part + counter_val.to_bytes(4, 'big')

    def _ctr_encrypt(self, data: bytes, initial_counter: bytes) -> bytes:
        """
        Обработка данных в режиме CTR.

        Args:
            data (bytes): Данные для шифрования/дешифрования.
            initial_counter (bytes): Начальное значение счетчика.

        Returns:
            bytes: Результат обработки.
        """
        result = bytearray()
        counter = initial_counter

        for i in range(0, len(data), self.BLOCK_SIZE):
            block = data[i:i + self.BLOCK_SIZE]
            keystream = self.cipher.encrypt(counter)

            for j, byte in enumerate(block):
                result.append(byte ^ keystream[j])

            counter = self._inc32(counter)

        return bytes(result)

    def encrypt(self, plaintext: bytes, aad: bytes = b"") -> bytes:
        """
        Шифрование данных с аутентификацией в режиме GCM.

        Args:
            plaintext (bytes): Открытый текст.
            aad (bytes): Дополнительные аутентифицированные данные.

        Returns:
            bytes: Nonce + шифртекст + тег.
        """
        j0 = self.nonce + b'\x00\x00\x00\x01'

        counter = self._inc32(j0)

        ciphertext = self._ctr_encrypt(plaintext, counter)

        ghash_result = self._ghash(aad, ciphertext)

        e_j0 = self.cipher.encrypt(j0)
        tag = bytes(a ^ b for a, b in zip(ghash_result, e_j0))

        return self.nonce + ciphertext + tag

    def decrypt(self, data: bytes, aad: bytes = b"", external_nonce: bytes = None) -> bytes:
        """
        Дешифрование данных с проверкой аутентификации в режиме GCM.

        Args:
            data (bytes): Данные для дешифрования.
            aad (bytes): Дополнительные аутентифицированные данные.
            external_nonce (bytes): Внешний nonce. Если None, извлекается из данных.

        Returns:
            bytes: Открытый текст.

        Raises:
            ValueError: Если данные слишком короткие или nonce некорректен.
            AuthenticationError: Если аутентификация не прошла.
        """
        if external_nonce is not None:
            if len(external_nonce) != self.NONCE_SIZE:
                raise ValueError(f"Nonce должен быть {self.NONCE_SIZE} байт, получено {len(external_nonce)}")

            nonce = external_nonce

            min_size = self.TAG_SIZE
            if len(data) < min_size:
                raise ValueError(f"Данные слишком маленькие: {len(data)} байт")

            tag = data[-self.TAG_SIZE:]
            ciphertext = data[:-self.TAG_SIZE]
        else:
            min_size = self.NONCE_SIZE + self.TAG_SIZE
            if len(data) < min_size:
                raise ValueError(f"Данные слишком маленькие: {len(data)} байт, минимум {min_size}")

            nonce = data[:self.NONCE_SIZE]
            tag = data[-self.TAG_SIZE:]
            ciphertext = data[self.NONCE_SIZE:-self.TAG_SIZE]

        self.nonce = nonce

        self._H = self._bytes_to_int(
            self.cipher.encrypt(bytes(self.BLOCK_SIZE))
        )

        j0 = nonce + b'\x00\x00\x00\x01'

        ghash_result = self._ghash(aad, ciphertext)
        e_j0 = self.cipher.encrypt(j0)
        expected_tag = bytes(a ^ b for a, b in zip(ghash_result, e_j0))

        if not self._constant_time_compare(tag, expected_tag):
            raise AuthenticationError(
                "Authentication failed: AAD mismatch or ciphertext tampered"
            )

        # Authentication passed - decrypt
        counter = self._inc32(j0)
        plaintext = self._ctr_encrypt(ciphertext, counter)

        return plaintext

    @staticmethod
    def _constant_time_compare(a: bytes, b: bytes) -> bool:
        """
        Сравнение байтовых последовательностей за константное время.

        Args:
            a (bytes): Первая последовательность.
            b (bytes): Вторая последовательность.

        Returns:
            bool: True если последовательности равны, иначе False.
        """
        if len(a) != len(b):
            return False
        result = 0
        for x, y in zip(a, b):
            result |= x ^ y
        return result == 0

    def encrypt_file(self, input_path, output_path, aad: bytes = b""):
        """
        Шифрование файла в режиме GCM.

        Args:
            input_path: Путь к исходному файлу.
            output_path: Путь к зашифрованному файлу.
            aad (bytes): Дополнительные аутентифицированные данные.

        Raises:
            CryptoOperationError: При ошибках ввода-вывода.
        """
        try:
            with open(input_path, 'rb') as f:
                plaintext = f.read()

            result = self.encrypt(plaintext, aad)

            with open(output_path, 'wb') as f:
                f.write(result)
        except (IOError, OSError) as e:
            raise CryptoOperationError(f"File I/O error: {e}")

    def decrypt_file(self, input_path, output_path, aad: bytes = b"", iv: bytes = None):
        """
        Дешифрование файла в режиме GCM.

        Args:
            input_path: Путь к зашифрованному файлу.
            output_path: Путь к расшифрованному файлу.
            aad (bytes): Дополнительные аутентифицированные данные.
            iv (bytes): Nonce. Если None, извлекается из файла.

        Raises:
            AuthenticationError: Если аутентификация не прошла.
            CryptoOperationError: При ошибках ввода-вывода.
        """
        try:
            with open(input_path, 'rb') as f:
                data = f.read()

            try:
                plaintext = self.decrypt(data, aad, external_nonce=iv)
            except AuthenticationError:
                output_file = Path(output_path)
                if output_file.exists():
                    output_file.unlink()
                raise

            with open(output_path, 'wb') as f:
                f.write(plaintext)

        except (IOError, OSError) as e:
            raise CryptoOperationError(f"File I/O error: {e}")