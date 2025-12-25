"""
Минимальные unit тесты для AES-OFB режима.
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

from cryptocoreedu.modes.OFBMode import OFBMode
from cryptocoreedu.exceptions import CryptoOperationError


class TestOFBMode(unittest.TestCase):
    """Основные тесты для OFB режима."""

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
        ofb = OFBMode(self.key)

        input_file = Path(self.temp_dir) / "plain.txt"
        encrypted_file = Path(self.temp_dir) / "encrypted.bin"
        decrypted_file = Path(self.temp_dir) / "decrypted.txt"

        original = b"Hello, World! Testing OFB mode encryption."
        with open(input_file, 'wb') as f:
            f.write(original)

        ofb.encrypt_file(input_file, encrypted_file)
        ofb.decrypt_file(encrypted_file, decrypted_file, iv=None)

        with open(decrypted_file, 'rb') as f:
            result = f.read()

        self.assertEqual(result, original)

    def test_roundtrip_various_sizes(self):
        """Тест roundtrip для разных размеров данных (потоковый режим)."""
        ofb = OFBMode(self.key)

        # OFB - потоковый режим, работает с любым размером
        test_sizes = [1, 5, 15, 16, 17, 31, 32, 100, 1000]

        for size in test_sizes:
            with self.subTest(size=size):
                input_file = Path(self.temp_dir) / f"plain_{size}.bin"
                encrypted_file = Path(self.temp_dir) / f"enc_{size}.bin"
                decrypted_file = Path(self.temp_dir) / f"dec_{size}.bin"

                original = os.urandom(size)
                with open(input_file, 'wb') as f:
                    f.write(original)

                ofb.encrypt_file(input_file, encrypted_file)
                ofb.decrypt_file(encrypted_file, decrypted_file, iv=None)

                with open(decrypted_file, 'rb') as f:
                    result = f.read()

                self.assertEqual(result, original)

    def test_stream_cipher_property(self):
        """Тест: OFB - потоковый режим (выход = вход по длине)."""
        ofb = OFBMode(self.key)

        # Не кратно 16
        original = b"12345"  # 5 байт

        input_file = Path(self.temp_dir) / "plain.bin"
        encrypted_file = Path(self.temp_dir) / "enc.bin"

        with open(input_file, 'wb') as f:
            f.write(original)

        ofb.encrypt_file(input_file, encrypted_file)

        with open(encrypted_file, 'rb') as f:
            ciphertext = f.read()

        # IV (16) + ciphertext (5) = 21 байт
        self.assertEqual(len(ciphertext), 16 + len(original))

    # ==================== NIST ВЕКТОР ====================

    @patch('cryptocoreedu.modes.OFBMode.generate_random_bytes')
    def test_nist_encrypt_vector(self, mock_random):
        """NIST SP 800-38A тест-вектор для AES-128-OFB (шифрование)."""
        nist_iv = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
        nist_plaintext = bytes.fromhex(
            "6bc1bee22e409f96e93d7e117393172a"
            "ae2d8a571e03ac9c9eb76fac45af8e51"
            "30c81c46a35ce411e5fbc1191a0a52ef"
            "f69f2445df4f9b17ad2b417be66c3710"
        )
        nist_ciphertext = bytes.fromhex(
            "3b3fd92eb72dad20333449f8e83cfb4a"
            "7789508d16918f03f53c52dac54ed825"
            "9740051e9c5fecf64344f7a82260edcc"
            "304c6528f659c77866a510d9c1d6ae5e"
        )

        mock_random.return_value = nist_iv

        ofb = OFBMode(self.key)

        input_file = Path(self.temp_dir) / "nist_plain.bin"
        encrypted_file = Path(self.temp_dir) / "nist_enc.bin"

        with open(input_file, 'wb') as f:
            f.write(nist_plaintext)

        ofb.encrypt_file(input_file, encrypted_file)

        with open(encrypted_file, 'rb') as f:
            result = f.read()

        # Проверяем IV и шифртекст
        self.assertEqual(result[:16], nist_iv)
        self.assertEqual(result[16:], nist_ciphertext)

    def test_nist_decrypt_vector(self):
        """NIST SP 800-38A тест-вектор для AES-128-OFB (дешифрование)."""
        nist_iv = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
        nist_plaintext = bytes.fromhex(
            "6bc1bee22e409f96e93d7e117393172a"
            "ae2d8a571e03ac9c9eb76fac45af8e51"
            "30c81c46a35ce411e5fbc1191a0a52ef"
            "f69f2445df4f9b17ad2b417be66c3710"
        )
        nist_ciphertext = bytes.fromhex(
            "3b3fd92eb72dad20333449f8e83cfb4a"
            "7789508d16918f03f53c52dac54ed825"
            "9740051e9c5fecf64344f7a82260edcc"
            "304c6528f659c77866a510d9c1d6ae5e"
        )

        ofb = OFBMode(self.key)

        encrypted_file = Path(self.temp_dir) / "nist_enc.bin"
        decrypted_file = Path(self.temp_dir) / "nist_dec.bin"

        # Записываем IV + ciphertext
        with open(encrypted_file, 'wb') as f:
            f.write(nist_iv + nist_ciphertext)

        ofb.decrypt_file(encrypted_file, decrypted_file, iv=None)

        with open(decrypted_file, 'rb') as f:
            result = f.read()

        self.assertEqual(result, nist_plaintext)

    def test_nist_single_block(self):
        """NIST тест-вектор: один блок."""
        nist_iv = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
        nist_plaintext = bytes.fromhex("6bc1bee22e409f96e93d7e117393172a")
        nist_ciphertext = bytes.fromhex("3b3fd92eb72dad20333449f8e83cfb4a")

        ofb = OFBMode(self.key)

        encrypted_file = Path(self.temp_dir) / "single_enc.bin"
        decrypted_file = Path(self.temp_dir) / "single_dec.bin"

        with open(encrypted_file, 'wb') as f:
            f.write(nist_iv + nist_ciphertext)

        ofb.decrypt_file(encrypted_file, decrypted_file, iv=None)

        with open(decrypted_file, 'rb') as f:
            result = f.read()

        self.assertEqual(result, nist_plaintext)

    # ==================== НЕГАТИВНЫЕ ТЕСТЫ ====================

    def test_file_not_found(self):
        """Тест: несуществующий файл."""
        ofb = OFBMode(self.key)

        with self.assertRaises(CryptoOperationError):
            ofb.encrypt_file(Path("/nonexistent/file.txt"), Path(self.temp_dir) / "out.bin")

    def test_decrypt_file_too_short(self):
        """Тест: файл короче IV (16 байт)."""
        ofb = OFBMode(self.key)

        short_file = Path(self.temp_dir) / "short.bin"
        with open(short_file, 'wb') as f:
            f.write(b"short")  # < 16 байт

        with self.assertRaises(CryptoOperationError):
            ofb.decrypt_file(short_file, Path(self.temp_dir) / "out.bin", iv=None)

    def test_decrypt_only_iv(self):
        """Тест: файл содержит только IV."""
        ofb = OFBMode(self.key)

        iv_only_file = Path(self.temp_dir) / "iv_only.bin"
        with open(iv_only_file, 'wb') as f:
            f.write(b"\x00" * 16)  # Только IV

        with self.assertRaises(CryptoOperationError):
            ofb.decrypt_file(iv_only_file, Path(self.temp_dir) / "out.bin", iv=None)

    def test_wrong_key_produces_garbage(self):
        """Тест: неверный ключ даёт мусор (OFB - потоковый режим)."""
        correct_key = self.key
        wrong_key = bytes.fromhex("00000000000000000000000000000000")

        ofb_enc = OFBMode(correct_key)
        ofb_dec = OFBMode(wrong_key)

        input_file = Path(self.temp_dir) / "plain.txt"
        encrypted_file = Path(self.temp_dir) / "enc.bin"
        decrypted_file = Path(self.temp_dir) / "dec.txt"

        original = b"Secret message!"
        with open(input_file, 'wb') as f:
            f.write(original)

        ofb_enc.encrypt_file(input_file, encrypted_file)

        # OFB - потоковый режим, нет padding -> нет ошибки, просто мусор
        ofb_dec.decrypt_file(encrypted_file, decrypted_file, iv=None)

        with open(decrypted_file, 'rb') as f:
            result = f.read()

        self.assertNotEqual(result, original)

    def test_bit_flip_isolated(self):
        """Тест: ошибка в одном бите влияет только на этот бит (свойство OFB)."""
        ofb = OFBMode(self.key)

        original = b"AAAAAAAAAAAAAAAA" * 4  # 64 байта

        input_file = Path(self.temp_dir) / "plain.bin"
        encrypted_file = Path(self.temp_dir) / "enc.bin"
        decrypted_file = Path(self.temp_dir) / "dec.bin"

        with open(input_file, 'wb') as f:
            f.write(original)

        ofb.encrypt_file(input_file, encrypted_file)

        # Меняем один бит в шифртексте (после IV)
        with open(encrypted_file, 'rb') as f:
            data = bytearray(f.read())

        flip_pos = 20  # Позиция в шифртексте (после 16-байтного IV)
        data[flip_pos] ^= 0x01

        with open(encrypted_file, 'wb') as f:
            f.write(bytes(data))

        ofb.decrypt_file(encrypted_file, decrypted_file, iv=None)

        with open(decrypted_file, 'rb') as f:
            result = f.read()

        # В OFB ошибка в одном бите влияет только на этот бит
        plaintext_pos = flip_pos - 16
        errors = sum(1 for i, (a, b) in enumerate(zip(original, result)) if a != b)
        self.assertEqual(errors, 1)  # Только один бит изменён

    def test_decrypt_with_explicit_iv(self):
        """Тест: дешифрование с явно переданным IV."""
        ofb = OFBMode(self.key)

        original = b"Test data for explicit IV"

        input_file = Path(self.temp_dir) / "plain.bin"
        encrypted_file = Path(self.temp_dir) / "enc.bin"
        decrypted_file = Path(self.temp_dir) / "dec.bin"

        with open(input_file, 'wb') as f:
            f.write(original)

        ofb.encrypt_file(input_file, encrypted_file)

        # Извлекаем IV и шифртекст
        with open(encrypted_file, 'rb') as f:
            file_iv = f.read(16)
            ciphertext = f.read()

        # Записываем только шифртекст
        with open(encrypted_file, 'wb') as f:
            f.write(ciphertext)

        # Дешифруем с явным IV
        ofb.decrypt_file(encrypted_file, decrypted_file, iv=file_iv)

        with open(decrypted_file, 'rb') as f:
            result = f.read()

        self.assertEqual(result, original)


if __name__ == '__main__':
    unittest.main(verbosity=2)