"""
Минимальные unit тесты для AES-ECB режима.
Покрывает: roundtrip, NIST вектор, негативные сценарии.
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from cryptocoreedu.modes.ECBMode import ECBMode
from cryptocoreedu.exceptions import CryptoOperationError


class TestECBMode(unittest.TestCase):
    """Основные тесты для ECB режима."""

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
        ecb = ECBMode(self.key)

        input_file = Path(self.temp_dir) / "plain.txt"
        encrypted_file = Path(self.temp_dir) / "encrypted.bin"
        decrypted_file = Path(self.temp_dir) / "decrypted.txt"

        original = b"Hello, World! Testing ECB mode encryption."
        with open(input_file, 'wb') as f:
            f.write(original)

        ecb.encrypt_file(input_file, encrypted_file)
        ecb.decrypt_file(encrypted_file, decrypted_file)

        with open(decrypted_file, 'rb') as f:
            result = f.read()

        self.assertEqual(result, original)

    def test_roundtrip_various_sizes(self):
        """Тест roundtrip для разных размеров данных."""
        ecb = ECBMode(self.key)

        test_sizes = [0, 1, 15, 16, 17, 32, 100, 1000]

        for size in test_sizes:
            with self.subTest(size=size):
                input_file = Path(self.temp_dir) / f"plain_{size}.bin"
                encrypted_file = Path(self.temp_dir) / f"enc_{size}.bin"
                decrypted_file = Path(self.temp_dir) / f"dec_{size}.bin"

                original = os.urandom(size) if size > 0 else b""
                with open(input_file, 'wb') as f:
                    f.write(original)

                ecb.encrypt_file(input_file, encrypted_file)
                ecb.decrypt_file(encrypted_file, decrypted_file)

                with open(decrypted_file, 'rb') as f:
                    result = f.read()

                self.assertEqual(result, original)

    # ==================== NIST ВЕКТОР ====================

    def test_nist_encrypt_vector(self):
        """NIST SP 800-38A тест-вектор для AES-128-ECB (шифрование)."""
        # NIST тестовые данные
        nist_plaintext = bytes.fromhex(
            "6bc1bee22e409f96e93d7e117393172a"
            "ae2d8a571e03ac9c9eb76fac45af8e51"
            "30c81c46a35ce411e5fbc1191a0a52ef"
            "f69f2445df4f9b17ad2b417be66c3710"
        )
        nist_ciphertext = bytes.fromhex(
            "3ad77bb40d7a3660a89ecaf32466ef97"
            "f5d3d58503b9699de785895a96fdbaaf"
            "43b1cd7f598ece23881b00e3ed030688"
            "7b0c785e27e8ad3f8223207104725dd4"
        )

        ecb = ECBMode(self.key)

        input_file = Path(self.temp_dir) / "nist_plain.bin"
        encrypted_file = Path(self.temp_dir) / "nist_enc.bin"

        with open(input_file, 'wb') as f:
            f.write(nist_plaintext)

        ecb.encrypt_file(input_file, encrypted_file)

        with open(encrypted_file, 'rb') as f:
            result = f.read()

        # Первые 64 байта должны совпадать (без учёта padding)
        self.assertEqual(result[:64], nist_ciphertext)


    def test_ecb_same_blocks_same_ciphertext(self):
        """Тест: одинаковые блоки дают одинаковый шифртекст (свойство ECB)."""
        ecb = ECBMode(self.key)

        # 3 одинаковых блока
        plaintext = b"AAAAAAAAAAAAAAAA" * 3  # 48 байт

        input_file = Path(self.temp_dir) / "same_blocks.bin"
        encrypted_file = Path(self.temp_dir) / "enc.bin"

        with open(input_file, 'wb') as f:
            f.write(plaintext)

        ecb.encrypt_file(input_file, encrypted_file)

        with open(encrypted_file, 'rb') as f:
            ciphertext = f.read()

        # Все блоки шифртекста должны быть одинаковыми
        block1 = ciphertext[0:16]
        block2 = ciphertext[16:32]
        block3 = ciphertext[32:48]

        self.assertEqual(block1, block2)
        self.assertEqual(block2, block3)

    # ==================== НЕГАТИВНЫЕ ТЕСТЫ ====================

    def test_file_not_found(self):
        """Тест: несуществующий файл."""
        ecb = ECBMode(self.key)

        with self.assertRaises(CryptoOperationError):
            ecb.encrypt_file(Path("/nonexistent/file.txt"), Path(self.temp_dir) / "out.bin")

    def test_decrypt_invalid_ciphertext_length(self):
        """Тест: некорректная длина шифртекста (не кратна 16)."""
        ecb = ECBMode(self.key)

        invalid_file = Path(self.temp_dir) / "invalid.bin"
        with open(invalid_file, 'wb') as f:
            f.write(b"\x00" * 17)  # Не кратно 16

        with self.assertRaises(CryptoOperationError):
            ecb.decrypt_file(invalid_file, Path(self.temp_dir) / "out.bin")

    def test_wrong_key_fails(self):
        """Тест: неверный ключ приводит к ошибке padding."""
        correct_key = self.key
        wrong_key = bytes.fromhex("00000000000000000000000000000000")

        ecb_enc = ECBMode(correct_key)
        ecb_dec = ECBMode(wrong_key)

        input_file = Path(self.temp_dir) / "plain.txt"
        encrypted_file = Path(self.temp_dir) / "enc.bin"
        decrypted_file = Path(self.temp_dir) / "dec.txt"

        with open(input_file, 'wb') as f:
            f.write(b"Secret message!")

        ecb_enc.encrypt_file(input_file, encrypted_file)

        with self.assertRaises(CryptoOperationError):
            ecb_dec.decrypt_file(encrypted_file, decrypted_file)

    def test_tampered_ciphertext_fails(self):
        """Тест: изменённый шифртекст приводит к ошибке."""
        ecb = ECBMode(self.key)

        input_file = Path(self.temp_dir) / "plain.txt"
        encrypted_file = Path(self.temp_dir) / "enc.bin"
        decrypted_file = Path(self.temp_dir) / "dec.txt"

        with open(input_file, 'wb') as f:
            f.write(b"Test message")

        ecb.encrypt_file(input_file, encrypted_file)

        # Портим последний байт
        with open(encrypted_file, 'r+b') as f:
            f.seek(-1, 2)
            byte = f.read(1)[0]
            f.seek(-1, 2)
            f.write(bytes([byte ^ 0xFF]))

        with self.assertRaises(CryptoOperationError):
            ecb.decrypt_file(encrypted_file, decrypted_file)

if __name__ == '__main__':
    unittest.main(verbosity=2)