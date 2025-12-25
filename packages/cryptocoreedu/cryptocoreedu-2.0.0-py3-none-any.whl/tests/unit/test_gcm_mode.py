"""
Минимальные unit тесты для AES-GCM режима.
Покрывает: roundtrip, NIST SP 800-38D векторы, негативные сценарии.
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from cryptocoreedu.modes.GCMMode import GCMMode
from cryptocoreedu.exceptions import AuthenticationError, CryptoOperationError


class TestGCMMode(unittest.TestCase):
    """Основные тесты для GCM режима."""

    def setUp(self):
        """Подготовка к тестам."""
        self.temp_dir = tempfile.mkdtemp()
        self.key_128 = bytes.fromhex("00000000000000000000000000000000")
        self.key_256 = bytes.fromhex("0000000000000000000000000000000000000000000000000000000000000000")

    def tearDown(self):
        """Очистка после тестов."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # ==================== ROUNDTRIP ТЕСТЫ ====================

    def test_encrypt_decrypt_roundtrip(self):
        """Тест: шифрование -> дешифрование = исходные данные."""
        gcm = GCMMode(self.key_128)

        plaintext = b"Hello, World! Testing GCM mode encryption."
        aad = b"additional authenticated data"

        ciphertext = gcm.encrypt(plaintext, aad)
        decrypted = gcm.decrypt(ciphertext, aad)

        self.assertEqual(decrypted, plaintext)

    def test_roundtrip_various_sizes(self):
        """Тест roundtrip для разных размеров данных."""
        gcm = GCMMode(self.key_128)

        test_sizes = [0, 1, 15, 16, 17, 32, 100, 1000]

        for size in test_sizes:
            with self.subTest(size=size):
                gcm = GCMMode(self.key_128)  # Новый nonce
                plaintext = os.urandom(size) if size > 0 else b""
                aad = b"test aad"

                ciphertext = gcm.encrypt(plaintext, aad)
                decrypted = gcm.decrypt(ciphertext, aad)

                self.assertEqual(decrypted, plaintext)

    def test_roundtrip_no_aad(self):
        """Тест roundtrip без AAD."""
        gcm = GCMMode(self.key_128)

        plaintext = b"Message without AAD"

        ciphertext = gcm.encrypt(plaintext)
        decrypted = gcm.decrypt(ciphertext)

        self.assertEqual(decrypted, plaintext)

    def test_file_roundtrip(self):
        """Тест: шифрование/дешифрование файла."""
        gcm = GCMMode(self.key_128)

        input_file = Path(self.temp_dir) / "plain.txt"
        encrypted_file = Path(self.temp_dir) / "encrypted.bin"
        decrypted_file = Path(self.temp_dir) / "decrypted.txt"

        original = b"File content for GCM encryption test."
        aad = b"file metadata"

        with open(input_file, 'wb') as f:
            f.write(original)

        gcm.encrypt_file(input_file, encrypted_file, aad)
        gcm.decrypt_file(encrypted_file, decrypted_file, aad)

        with open(decrypted_file, 'rb') as f:
            result = f.read()

        self.assertEqual(result, original)

    # ==================== NIST SP 800-38D ВЕКТОРЫ ====================

    @patch('cryptocoreedu.modes.GCMMode.generate_random_bytes')
    def test_nist_vector_1(self, mock_random):
        """NIST SP 800-38D Test Case 1: 128-bit key, no plaintext, no AAD."""
        key = bytes.fromhex("00000000000000000000000000000000")
        nonce = bytes.fromhex("000000000000000000000000")
        plaintext = b""
        aad = b""
        expected_tag = bytes.fromhex("58e2fccefa7e3061367f1d57a4e7455a")

        mock_random.return_value = nonce

        gcm = GCMMode(key)
        result = gcm.encrypt(plaintext, aad)

        # Result = nonce (12) + ciphertext (0) + tag (16)
        result_nonce = result[:12]
        result_tag = result[-16:]

        self.assertEqual(result_nonce, nonce)
        self.assertEqual(result_tag, expected_tag)

    @patch('cryptocoreedu.modes.GCMMode.generate_random_bytes')
    def test_nist_vector_2(self, mock_random):
        """NIST SP 800-38D Test Case 2: 128-bit key, 128-bit plaintext, no AAD."""
        key = bytes.fromhex("00000000000000000000000000000000")
        nonce = bytes.fromhex("000000000000000000000000")
        plaintext = bytes.fromhex("00000000000000000000000000000000")
        aad = b""
        expected_ciphertext = bytes.fromhex("0388dace60b6a392f328c2b971b2fe78")
        expected_tag = bytes.fromhex("ab6e47d42cec13bdf53a67b21257bddf")

        mock_random.return_value = nonce

        gcm = GCMMode(key)
        result = gcm.encrypt(plaintext, aad)

        result_nonce = result[:12]
        result_ciphertext = result[12:-16]
        result_tag = result[-16:]

        self.assertEqual(result_nonce, nonce)
        self.assertEqual(result_ciphertext, expected_ciphertext)
        self.assertEqual(result_tag, expected_tag)

    @patch('cryptocoreedu.modes.GCMMode.generate_random_bytes')
    def test_nist_vector_3(self, mock_random):
        """NIST SP 800-38D Test Case 3: with AAD."""
        key = bytes.fromhex("feffe9928665731c6d6a8f9467308308")
        nonce = bytes.fromhex("cafebabefacedbaddecaf888")
        plaintext = bytes.fromhex(
            "d9313225f88406e5a55909c5aff5269a"
            "86a7a9531534f7da2e4c303d8a318a72"
            "1c3c0c95956809532fcf0e2449a6b525"
            "b16aedf5aa0de657ba637b391aafd255"
        )
        aad = b""
        expected_ciphertext = bytes.fromhex(
            "42831ec2217774244b7221b784d0d49c"
            "e3aa212f2c02a4e035c17e2329aca12e"
            "21d514b25466931c7d8f6a5aac84aa05"
            "1ba30b396a0aac973d58e091473f5985"
        )
        expected_tag = bytes.fromhex("4d5c2af327cd64a62cf35abd2ba6fab4")

        mock_random.return_value = nonce

        gcm = GCMMode(key)
        result = gcm.encrypt(plaintext, aad)

        result_ciphertext = result[12:-16]
        result_tag = result[-16:]

        self.assertEqual(result_ciphertext, expected_ciphertext)
        self.assertEqual(result_tag, expected_tag)

    def test_nist_decrypt_vector(self):
        """NIST тест-вектор: дешифрование."""
        key = bytes.fromhex("00000000000000000000000000000000")
        nonce = bytes.fromhex("000000000000000000000000")
        ciphertext = bytes.fromhex("0388dace60b6a392f328c2b971b2fe78")
        tag = bytes.fromhex("ab6e47d42cec13bdf53a67b21257bddf")
        expected_plaintext = bytes.fromhex("00000000000000000000000000000000")

        gcm = GCMMode(key)

        # Формат: nonce + ciphertext + tag
        data = nonce + ciphertext + tag

        result = gcm.decrypt(data, aad=b"")

        self.assertEqual(result, expected_plaintext)

    # ==================== ФОРМАТ ВЫХОДА ====================

    def test_output_format(self):
        """Тест: правильный формат выхода (nonce + ciphertext + tag)."""
        gcm = GCMMode(self.key_128)

        plaintext = b"Test message"
        result = gcm.encrypt(plaintext)

        # nonce (12) + ciphertext (12) + tag (16) = 40 байт
        expected_len = gcm.NONCE_SIZE + len(plaintext) + gcm.TAG_SIZE
        self.assertEqual(len(result), expected_len)

    def test_different_nonces_different_output(self):
        """Тест: разные nonce дают разный шифртекст."""
        plaintext = b"Same message"
        aad = b"same aad"

        gcm1 = GCMMode(self.key_128)
        gcm2 = GCMMode(self.key_128)

        ct1 = gcm1.encrypt(plaintext, aad)
        ct2 = gcm2.encrypt(plaintext, aad)

        self.assertNotEqual(ct1, ct2)

    # ==================== КЛЮЧИ ====================

    def test_different_key_sizes(self):
        """Тест: поддержка разных размеров ключей."""
        key_192 = bytes.fromhex("000000000000000000000000000000000000000000000000")

        for key in [self.key_128, key_192, self.key_256]:
            with self.subTest(key_len=len(key)):
                gcm = GCMMode(key)

                plaintext = b"Test message"
                ciphertext = gcm.encrypt(plaintext)
                decrypted = gcm.decrypt(ciphertext)

                self.assertEqual(decrypted, plaintext)

    def test_invalid_key_size(self):
        """Тест: неверный размер ключа."""
        with self.assertRaises(ValueError):
            GCMMode(b"short")

    def test_invalid_nonce_size(self):
        """Тест: неверный размер nonce."""
        with self.assertRaises(ValueError):
            GCMMode(self.key_128, nonce=b"short")

    # ==================== НЕГАТИВНЫЕ ТЕСТЫ ====================

    def test_tampered_ciphertext_fails(self):
        """Тест: изменённый шифртекст не проходит аутентификацию."""
        gcm = GCMMode(self.key_128)

        plaintext = b"Secret message"
        ciphertext = bytearray(gcm.encrypt(plaintext))

        # Портим байт в середине
        ciphertext[15] ^= 0x01

        with self.assertRaises(AuthenticationError):
            gcm.decrypt(bytes(ciphertext))

    def test_tampered_tag_fails(self):
        """Тест: изменённый тег не проходит аутентификацию."""
        gcm = GCMMode(self.key_128)

        plaintext = b"Secret message"
        ciphertext = bytearray(gcm.encrypt(plaintext))

        # Портим последний байт (тег)
        ciphertext[-1] ^= 0x01

        with self.assertRaises(AuthenticationError):
            gcm.decrypt(bytes(ciphertext))

    def test_tampered_nonce_fails(self):
        """Тест: изменённый nonce не проходит аутентификацию."""
        gcm = GCMMode(self.key_128)

        plaintext = b"Secret message"
        ciphertext = bytearray(gcm.encrypt(plaintext))

        # Портим первый байт (nonce)
        ciphertext[0] ^= 0x01

        with self.assertRaises(AuthenticationError):
            gcm.decrypt(bytes(ciphertext))

    def test_wrong_aad_fails(self):
        """Тест: неверный AAD не проходит аутентификацию."""
        gcm = GCMMode(self.key_128)

        plaintext = b"Secret message"
        aad = b"correct aad"

        ciphertext = gcm.encrypt(plaintext, aad)

        with self.assertRaises(AuthenticationError):
            gcm.decrypt(ciphertext, b"wrong aad")

    def test_truncated_data_fails(self):
        """Тест: обрезанные данные."""
        gcm = GCMMode(self.key_128)

        plaintext = b"Secret message"
        ciphertext = gcm.encrypt(plaintext)

        # Обрезаем данные
        truncated = ciphertext[:20]

        with self.assertRaises(ValueError):
            gcm.decrypt(truncated)

    def test_file_not_found(self):
        """Тест: несуществующий файл."""
        gcm = GCMMode(self.key_128)

        with self.assertRaises(CryptoOperationError):
            gcm.encrypt_file("/nonexistent/file.txt", Path(self.temp_dir) / "out.bin")

    def test_file_auth_failure_deletes_output(self):
        """Тест: при ошибке аутентификации выходной файл удаляется."""
        gcm = GCMMode(self.key_128)

        input_file = Path(self.temp_dir) / "plain.txt"
        encrypted_file = Path(self.temp_dir) / "enc.bin"
        decrypted_file = Path(self.temp_dir) / "dec.txt"

        with open(input_file, 'wb') as f:
            f.write(b"Test message")

        gcm.encrypt_file(input_file, encrypted_file, aad=b"correct")

        with self.assertRaises(AuthenticationError):
            gcm.decrypt_file(encrypted_file, decrypted_file, aad=b"wrong")

        self.assertFalse(decrypted_file.exists())

    def test_constant_time_compare(self):
        """Тест: функция сравнения за константное время."""
        self.assertTrue(GCMMode._constant_time_compare(b"test", b"test"))
        self.assertFalse(GCMMode._constant_time_compare(b"test", b"Test"))
        self.assertFalse(GCMMode._constant_time_compare(b"test", b"testing"))

    # ==================== EXTERNAL NONCE ====================

    def test_decrypt_with_external_nonce(self):
        """Тест: дешифрование с внешним nonce."""
        gcm = GCMMode(self.key_128)

        plaintext = b"Test message"
        result = gcm.encrypt(plaintext)

        # Извлекаем nonce
        nonce = result[:12]
        ciphertext_with_tag = result[12:]

        # Дешифруем с внешним nonce
        decrypted = gcm.decrypt(ciphertext_with_tag, external_nonce=nonce)

        self.assertEqual(decrypted, plaintext)


if __name__ == '__main__':
    unittest.main(verbosity=2)