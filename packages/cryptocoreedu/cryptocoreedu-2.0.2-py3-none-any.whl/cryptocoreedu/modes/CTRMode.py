from Crypto.Cipher import AES
from pathlib import Path

from ..file_io import read_file, write_file
from ..exceptions import CryptoOperationError
from ..csprng import generate_random_bytes


class CTRMode:
    """
    Реализация режима CTR (Counter) для AES-128 как потокового шифра.

    Атрибуты:
        BLOCK_SIZE (int): Размер блока AES в байтах (16 байт).
    """

    BLOCK_SIZE = 16

    def __init__(self, key: bytes):
        """
        Инициализация режима CTR с ключом.

        Args:
            key (bytes): Ключ для шифрования AES-128 (16 байт).
        """
        self.key = key
        # Создаем базовый cipher для шифрования отдельных блоков
        self.cipher = AES.new(self.key, AES.MODE_ECB)

    def _increment_counter(self, counter: bytes) -> bytes:
        """
        Инкрементирование счетчика на 1.

        Args:
            counter (bytes): Текущее значение счетчика (16 байт).

        Returns:
            bytes: Увеличенное значение счетчика.
        """
        counter_int = int.from_bytes(counter, byteorder='big')
        counter_int = (counter_int + 1) & ((1 << 128) - 1)
        return counter_int.to_bytes(16, byteorder='big')

    def encrypt_file(self, input_file: Path, output_file: Path) -> None:
        """
        Шифрование файла в режиме CTR.

        Args:
            input_file (Path): Путь к исходному файлу.
            output_file (Path): Путь к зашифрованному файлу.

        Raises:
            CryptoOperationError: При ошибках шифрования или ввода-вывода.
        """
        try:
            plaintext = read_file(input_file)

            iv = generate_random_bytes(self.BLOCK_SIZE)

            # Проверяем корректность IV
            if len(iv) != self.BLOCK_SIZE:
                raise CryptoOperationError(f"IV должен быть длиной {self.BLOCK_SIZE} байт")

            encrypted_blocks = []
            counter = iv

            # Обрабатываем данные блоками
            for i in range(0, len(plaintext), self.BLOCK_SIZE):
                block = plaintext[i:i + self.BLOCK_SIZE]

                # Шифруем текущее значение счетчика для получения keystream
                keystream = self.cipher.encrypt(counter)

                # XOR plaintext с keystream для получения ciphertext
                ciphertext_block = bytes(a ^ b for a, b in zip(block, keystream[:len(block)]))
                encrypted_blocks.append(ciphertext_block)

                # Инкрементируем счетчик для следующего блока
                counter = self._increment_counter(counter)

            # Записываем IV (nonce) и зашифрованные данные
            write_file(output_file, iv + b''.join(encrypted_blocks))

        except (FileNotFoundError, ValueError, IOError) as error:
            raise CryptoOperationError(f"Ошибка при шифровании режимом CTR: {error}")
        except Exception as error:
            raise CryptoOperationError(f"Неизвестная ошибка при шифровании CTR: {error}")

    def decrypt_file(self, input_file: Path, output_file: Path, iv: bytes) -> None:
        """
        Дешифрование файла в режиме CTR.

        Args:
            input_file (Path): Путь к зашифрованному файлу.
            output_file (Path): Путь к расшифрованному файлу.
            iv (bytes): Вектор инициализации (nonce). Если None, извлекается из файла.

        Raises:
            CryptoOperationError: При ошибках дешифрования или ввода-вывода.
        """
        try:
            ciphertext = read_file(input_file)

            # Проверяем минимальный размер данных
            if len(ciphertext) < self.BLOCK_SIZE:
                raise CryptoOperationError("Файл слишком короткий для CTR режима")

            if iv is None:
                file_iv = ciphertext[:self.BLOCK_SIZE]
                ciphertext_blocks = ciphertext[self.BLOCK_SIZE:]
            else:
                file_iv = iv
                ciphertext_blocks = ciphertext

            # Проверяем что после извлечения IV остались данные
            if len(ciphertext_blocks) == 0:
                raise CryptoOperationError("Файл не содержит данных для дешифрования")

            decrypted_blocks = []
            counter = file_iv

            # Обрабатываем данные блоками
            for i in range(0, len(ciphertext_blocks), self.BLOCK_SIZE):
                block = ciphertext_blocks[i:i + self.BLOCK_SIZE]

                # Шифруем текущее значение счетчика для получения keystream
                keystream = self.cipher.encrypt(counter)

                # XOR ciphertext с keystream для получения plaintext
                plaintext_block = bytes(a ^ b for a, b in zip(block, keystream[:len(block)]))
                decrypted_blocks.append(plaintext_block)

                # Инкрементируем счетчик для следующего блока
                counter = self._increment_counter(counter)

            # Объединяем расшифрованные блоки (без паддинга в CTR)
            decrypted_data = b''.join(decrypted_blocks)
            write_file(output_file, decrypted_data)

        except (FileNotFoundError, ValueError, IOError) as error:
            raise CryptoOperationError(f"Ошибка при дешифровании режимом CTR: {error}")
        except Exception as error:
            raise CryptoOperationError(f"Неизвестная ошибка при дешифровании CTR: {error}")