import os

from Crypto.Cipher import AES
from pathlib import Path

from ..file_io import read_file, write_file
from ..utils import PKCS7Padding
from ..exceptions import CryptoOperationError
from ..csprng import generate_random_bytes


class CBCMode:
    """
    Реализация режима CBC (Cipher Block Chaining) для AES-128 с паддингом PKCS7.

    Атрибуты:
        BLOCK_SIZE (int): Размер блока AES в байтах (16 байт).
    """

    BLOCK_SIZE = 16

    def __init__(self, key: bytes):
        """
        Инициализация режима CBC с ключом.

        Args:
            key (bytes): Ключ для шифрования AES-128 (16 байт).
        """
        self.key = key
        self.cipher = AES.new(self.key, AES.MODE_ECB)
        self.padding = PKCS7Padding

    def encrypt_file(self, input_file: Path, output_file: Path) -> None:
        """
        Шифрование файла в режиме CBC.

        Args:
            input_file (Path): Путь к исходному файлу.
            output_file (Path): Путь к зашифрованному файлу.

        Raises:
            CryptoOperationError: При ошибках шифрования или ввода-вывода.
        """
        try:
            plaintext = read_file(input_file)
            padded_data = self.padding.pad(plaintext)

            # Генерируем случайный IV если не предоставлен

            iv = generate_random_bytes(self.BLOCK_SIZE)

            # Проверяем корректность IV
            if len(iv) != self.BLOCK_SIZE:
                raise CryptoOperationError(f"IV должен быть длиной {self.BLOCK_SIZE} байт")

            encrypted_blocks = []
            previous_block = iv

            # Шифруем блоки в режиме CBC
            for i in range(0, len(padded_data), self.BLOCK_SIZE):
                block = padded_data[i:i + self.BLOCK_SIZE]

                # XOR с предыдущим зашифрованным блоком (или IV для первого блока)
                xor_block = bytes(a ^ b for a, b in zip(block, previous_block))

                # Шифруем результат XOR
                encrypted_block = self.cipher.encrypt(xor_block)
                encrypted_blocks.append(encrypted_block)
                previous_block = encrypted_block

            # Записываем IV и зашифрованные данные
            write_file(output_file, iv + b''.join(encrypted_blocks))

        except (FileNotFoundError, ValueError, IOError) as error:
            raise CryptoOperationError(f"Ошибка при шифровании режимом CBC: {error}")
        except Exception as error:
            raise CryptoOperationError(f"Неизвестная ошибка при шифровании CBC: {error}")

    def decrypt_file(self, input_file: Path, output_file: Path, iv: bytes) -> None:
        """
        Дешифрование файла в режиме CBC.

        Args:
            input_file (Path): Путь к зашифрованному файлу.
            output_file (Path): Путь к расшифрованному файлу.
            iv (bytes): Вектор инициализации (IV). Если None, извлекается из файла.

        Raises:
            CryptoOperationError: При ошибках дешифрования или ввода-вывода.
        """
        try:
            ciphertext = read_file(input_file)

            # Проверяем минимальный размер данных
            if len(ciphertext) < self.BLOCK_SIZE:
                raise CryptoOperationError("Файл слишком короткий для CBC режима")

            # Извлекаем IV из начала файла или используем предоставленный
            if iv is None:
                # Если IV не предоставлен, извлекаем из файла
                file_iv = ciphertext[:self.BLOCK_SIZE]
                ciphertext_blocks = ciphertext[self.BLOCK_SIZE:]
            else:
                # Используем предоставленный IV
                file_iv = iv
                ciphertext_blocks = ciphertext

            if len(ciphertext_blocks) == 0:
                raise CryptoOperationError("Файл не содержит данных для дешифрования")

            if len(ciphertext_blocks) % self.BLOCK_SIZE != 0:
                raise CryptoOperationError("Некорректный размер шифртекста")

            decrypted_blocks = []
            previous_block = file_iv

            # Дешифруем блоки в режиме CBC
            for i in range(0, len(ciphertext_blocks), self.BLOCK_SIZE):
                block = ciphertext_blocks[i:i + self.BLOCK_SIZE]

                # Дешифруем блок
                decrypted_block = self.cipher.decrypt(block)

                # XOR с предыдущим зашифрованным блоком (или IV для первого блока)
                plain_block = bytes(a ^ b for a, b in zip(decrypted_block, previous_block))

                decrypted_blocks.append(plain_block)
                previous_block = block

            # Объединяем и удаляем паддинг
            decrypted_data = b''.join(decrypted_blocks)
            unpadded_data = self.padding.unpad(decrypted_data)

            write_file(output_file, unpadded_data)

        except (FileNotFoundError, ValueError, IOError) as error:
            raise CryptoOperationError(f"Ошибка при дешифровании режимом CBC: {error}")
        except Exception as error:
            raise CryptoOperationError(f"Неизвестная ошибка при дешифровании CBC: {error}")