from Crypto.Cipher import AES
from pathlib import Path

from ..file_io import read_file, write_file
from ..exceptions import CryptoOperationError
from ..csprng import generate_random_bytes


class OFBMode:
    """
    Реализация режима OFB (Output Feedback) для AES-128 как потокового шифра.

    Атрибуты:
        BLOCK_SIZE (int): Размер блока AES в байтах (16 байт).
    """

    BLOCK_SIZE = 16

    def __init__(self, key: bytes):
        """
        Инициализация режима OFB с ключом.

        Args:
            key (bytes): Ключ для шифрования AES-128 (16 байт).
        """
        self.key = key
        self.cipher = AES.new(self.key, AES.MODE_ECB)

    def encrypt_file(self, input_file: Path, output_file: Path) -> None:
        """
        Шифрование файла в режиме OFB.

        Args:
            input_file (Path): Путь к исходному файлу.
            output_file (Path): Путь к зашифрованному файлу.

        Raises:
            CryptoOperationError: При ошибках шифрования или ввода-вывода.
        """
        try:
            plaintext = read_file(input_file)

            iv = generate_random_bytes(self.BLOCK_SIZE)

            if len(iv) != self.BLOCK_SIZE:
                raise CryptoOperationError(f"IV должен быть длиной {self.BLOCK_SIZE} байт")

            encrypted_blocks = []
            feedback = iv

            for i in range(0, len(plaintext), self.BLOCK_SIZE):
                block = plaintext[i:i + self.BLOCK_SIZE]

                # Шифруем feedback для получения keystream
                keystream = self.cipher.encrypt(feedback)

                # XOR plaintext с keystream для получения ciphertext
                ciphertext_block = bytes(a ^ b for a, b in zip(block, keystream[:len(block)]))
                encrypted_blocks.append(ciphertext_block)

                feedback = keystream

            write_file(output_file, iv + b''.join(encrypted_blocks))

        except (FileNotFoundError, ValueError, IOError) as error:
            raise CryptoOperationError(f"Ошибка при шифровании режимом OFB: {error}")
        except Exception as error:
            raise CryptoOperationError(f"Неизвестная ошибка при шифровании OFB: {error}")

    def decrypt_file(self, input_file: Path, output_file: Path, iv: bytes) -> None:
        """
        Дешифрование файла в режиме OFB.

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
                raise CryptoOperationError("Файл слишком короткий для OFB режима")

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
            feedback = file_iv

            for i in range(0, len(ciphertext_blocks), self.BLOCK_SIZE):
                block = ciphertext_blocks[i:i + self.BLOCK_SIZE]

                # Шифруем feedback для получения keystream
                keystream = self.cipher.encrypt(feedback)

                # XOR ciphertext с keystream для получения plaintext
                plaintext_block = bytes(a ^ b for a, b in zip(block, keystream[:len(block)]))
                decrypted_blocks.append(plaintext_block)

                feedback = keystream

            decrypted_data = b''.join(decrypted_blocks)
            write_file(output_file, decrypted_data)

        except (FileNotFoundError, ValueError, IOError) as error:
            raise CryptoOperationError(f"Ошибка при дешифровании режимом OFB: {error}")
        except Exception as error:
            raise CryptoOperationError(f"Неизвестная ошибка при дешифровании OFB: {error}")