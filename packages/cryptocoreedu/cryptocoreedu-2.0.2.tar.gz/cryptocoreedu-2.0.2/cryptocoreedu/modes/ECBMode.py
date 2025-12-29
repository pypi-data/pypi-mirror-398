from Crypto.Cipher import AES
from pathlib import Path

from ..file_io import read_file, write_file
from ..utils import PKCS7Padding
from ..exceptions import CryptoOperationError

import sys


class ECBMode:
    """
    Реализация режима ECB (Electronic Codebook) для AES-128 с паддингом PKCS7.

    Атрибуты:
        BLOCK_SIZE (int): Размер блока AES в байтах (16 байт).
    """

    BLOCK_SIZE = 16

    def __init__(self, key: bytes):
        """
        Инициализация режима ECB с ключом.

        Args:
            key (bytes): Ключ для шифрования AES-128 (16 байт).
        """
        self.key = key
        self.cipher = AES.new(self.key, AES.MODE_ECB)
        self.padding = PKCS7Padding

    def encrypt_file(self, input_file: Path, output_file: Path) -> None:
        """
        Шифрование файла в режиме ECB.

        Args:
            input_file (Path): Путь к исходному файлу.
            output_file (Path): Путь к зашифрованному файлу.

        Raises:
            CryptoOperationError: При ошибках шифрования или ввода-вывода.
        """
        try:
            plaintext = read_file(input_file)
            padded_data = self.padding.pad(plaintext)

            encrypted_blocks = []
            for i in range(0, len(padded_data), self.BLOCK_SIZE):
                block = padded_data[i:i + self.BLOCK_SIZE]
                encrypted_block = self.cipher.encrypt(block)
                encrypted_blocks.append(encrypted_block)

            write_file(output_file, b''.join(encrypted_blocks))

        except (FileNotFoundError, ValueError, IOError) as error:
            raise CryptoOperationError(f'Ошибка при шифровании режимом ECB: {error}')
        except Exception as error:
            raise CryptoOperationError(f"Неизвестная ошибка при шифровании ECB: {error}")

    def decrypt_file(self, input_file: Path, output_file: Path) -> None:
        """
        Дешифрование файла в режиме ECB.

        Args:
            input_file (Path): Путь к зашифрованному файлу.
            output_file (Path): Путь к расшифрованному файлу.

        Raises:
            CryptoOperationError: При ошибках дешифрования или ввода-вывода.
        """
        try:
            ciphertext = read_file(input_file)

            if len(ciphertext) % self.BLOCK_SIZE != 0:
                raise CryptoOperationError('Некорректный размер шифртекста для ECB')

            decrypted_blocks = []
            for i in range(0, len(ciphertext), self.BLOCK_SIZE):
                block = ciphertext[i:i + self.BLOCK_SIZE]
                decrypted_block = self.cipher.decrypt(block)
                decrypted_blocks.append(decrypted_block)

            decrypted_data = b''.join(decrypted_blocks)
            unpadded_data = self.padding.unpad(decrypted_data)

            write_file(output_file, unpadded_data)

        except (FileNotFoundError, ValueError, IOError) as error:
            raise CryptoOperationError(f"Ошибка при дешифровании режимом ECB: {error}")
        except Exception as error:
            raise CryptoOperationError(f"Неизвестная ошибка при дешифровании ECB: {error}")