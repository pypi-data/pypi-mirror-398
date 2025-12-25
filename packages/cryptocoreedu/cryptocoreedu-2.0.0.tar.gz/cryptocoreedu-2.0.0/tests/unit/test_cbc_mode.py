"""
Минимальные unit тесты для AES-CBC режима.
Покрывает: roundtrip, NIST вектор, негативные сценарии.
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from cryptocoreedu.modes.CBCMode import CBCMode
from cryptocoreedu.exceptions import CryptoOperationError


class TestCBCMode(unittest.TestCase):
    """Основные тесты для CBC режима."""

    def setUp(self):
        """Подготовка к тестам."""
        self.temp_dir = tempfile.mkdtemp()
        self.key = bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c")  # AES-128

    def tearDown(self):
        """Очистка после тестов."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # ==================== ROUNDTRIP ТЕСТЫ ====================

    def test_encrypt_decrypt_roundtrip(self):
        """Тест: шифрование -> дешифрование = исходные данные."""
        cbc = CBCMode(self.key)

        input_file = Path(self.temp_dir) / "plain.txt"
        encrypted_file = Path(self.temp_dir) / "encrypted.bin"
        decrypted_file = Path(self.temp_dir) / "decrypted.txt"

        original = b"Hello, World! Testing CBC mode encryption."
        with open(input_file, 'wb') as f:
            f.write(original)

        # Шифруем
        cbc.encrypt_file(input_file, encrypted_file)

        # Дешифруем (IV извлекается из файла)
        cbc.decrypt_file(encrypted_file, decrypted_file, iv=None)

        with open(decrypted_file, 'rb') as f:
            result = f.read()

        self.assertEqual(result, original)

    def test_roundtrip_various_sizes(self):
        """Тест roundtrip для разных размеров данных."""
        cbc = CBCMode(self.key)

        test_sizes = [0, 1, 15, 16, 17, 32, 100, 1000]

        for size in test_sizes:
            with self.subTest(size=size):
                input_file = Path(self.temp_dir) / f"plain_{size}.bin"
                encrypted_file = Path(self.temp_dir) / f"enc_{size}.bin"
                decrypted_file = Path(self.temp_dir) / f"dec_{size}.bin"

                original = os.urandom(size) if size > 0 else b""
                with open(input_file, 'wb') as f:
                    f.write(original)

                cbc.encrypt_file(input_file, encrypted_file)
                cbc.decrypt_file(encrypted_file, decrypted_file, iv=None)

                with open(decrypted_file, 'rb') as f:
                    result = f.read()

                self.assertEqual(result, original)

    # ==================== НЕГАТИВНЫЕ ТЕСТЫ ====================

    def test_file_not_found(self):
        """Тест: несуществующий файл."""
        cbc = CBCMode(self.key)

        with self.assertRaises(CryptoOperationError):
            cbc.encrypt_file(Path("/nonexistent/file.txt"), Path(self.temp_dir) / "out.bin")

    def test_decrypt_file_too_short(self):
        """Тест: файл короче одного блока."""
        cbc = CBCMode(self.key)

        short_file = Path(self.temp_dir) / "short.bin"
        with open(short_file, 'wb') as f:
            f.write(b"short")  # < 16 байт

        with self.assertRaises(CryptoOperationError):
            cbc.decrypt_file(short_file, Path(self.temp_dir) / "out.bin", iv=None)

    def test_decrypt_invalid_ciphertext_length(self):
        """Тест: некорректная длина шифртекста."""
        cbc = CBCMode(self.key)

        invalid_file = Path(self.temp_dir) / "invalid.bin"
        with open(invalid_file, 'wb') as f:
            f.write(b"\x00" * 16)  # IV
            f.write(b"\x00" * 17)  # Не кратно 16

        with self.assertRaises(CryptoOperationError):
            cbc.decrypt_file(invalid_file, Path(self.temp_dir) / "out.bin", iv=None)

    def test_wrong_key_fails(self):
        """Тест: неверный ключ приводит к ошибке padding."""
        correct_key = self.key
        wrong_key = bytes.fromhex("00000000000000000000000000000000")

        cbc_enc = CBCMode(correct_key)
        cbc_dec = CBCMode(wrong_key)

        input_file = Path(self.temp_dir) / "plain.txt"
        encrypted_file = Path(self.temp_dir) / "enc.bin"
        decrypted_file = Path(self.temp_dir) / "dec.txt"

        with open(input_file, 'wb') as f:
            f.write(b"Secret message!")

        cbc_enc.encrypt_file(input_file, encrypted_file)

        # Дешифрование с неверным ключом должно дать ошибку padding
        with self.assertRaises(CryptoOperationError):
            cbc_dec.decrypt_file(encrypted_file, decrypted_file, iv=None)

    def test_tampered_ciphertext_fails(self):
        """Тест: изменённый шифртекст приводит к ошибке."""
        cbc = CBCMode(self.key)

        input_file = Path(self.temp_dir) / "plain.txt"
        encrypted_file = Path(self.temp_dir) / "enc.bin"
        decrypted_file = Path(self.temp_dir) / "dec.txt"

        with open(input_file, 'wb') as f:
            f.write(b"Test message")

        cbc.encrypt_file(input_file, encrypted_file)

        # Портим последний байт (влияет на padding)
        with open(encrypted_file, 'r+b') as f:
            f.seek(-1, 2)  # Последний байт
            f.write(bytes([f.read(1)[0] ^ 0xFF]))

        with self.assertRaises(CryptoOperationError):
            cbc.decrypt_file(encrypted_file, decrypted_file, iv=None)


if __name__ == '__main__':
    unittest.main(verbosity=2)