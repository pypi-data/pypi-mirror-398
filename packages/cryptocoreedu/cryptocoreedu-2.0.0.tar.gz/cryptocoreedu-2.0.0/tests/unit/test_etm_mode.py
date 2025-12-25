"""
Минимальные unit тесты для ETM (Encrypt-then-MAC) режима.
Покрывает: roundtrip, аутентификация, негативные сценарии.
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from cryptocoreedu.modes.ETMMode import ETMMode
from cryptocoreedu.exceptions import AuthenticationError, CryptoOperationError


class TestETMMode(unittest.TestCase):
    """Основные тесты для ETM режима."""

    def setUp(self):
        """Подготовка к тестам."""
        self.temp_dir = tempfile.mkdtemp()
        self.key_128 = bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c")  # AES-128
        self.key_256 = bytes.fromhex("603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4")  # AES-256

    def tearDown(self):
        """Очистка после тестов."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # ==================== ROUNDTRIP ТЕСТЫ ====================

    def test_encrypt_decrypt_roundtrip(self):
        """Тест: шифрование -> дешифрование = исходные данные."""
        etm = ETMMode(self.key_128)

        plaintext = b"Hello, World! Testing ETM mode encryption with authentication."
        aad = b"additional authenticated data"

        ciphertext = etm.encrypt(plaintext, aad)
        decrypted = etm.decrypt(ciphertext, aad)

        self.assertEqual(decrypted, plaintext)

    def test_roundtrip_various_sizes(self):
        """Тест roundtrip для разных размеров данных."""
        etm = ETMMode(self.key_128)

        test_sizes = [0, 1, 15, 16, 17, 32, 100, 1000]

        for size in test_sizes:
            with self.subTest(size=size):
                plaintext = os.urandom(size) if size > 0 else b""
                aad = b"test aad"

                ciphertext = etm.encrypt(plaintext, aad)
                decrypted = etm.decrypt(ciphertext, aad)

                self.assertEqual(decrypted, plaintext)

    def test_roundtrip_no_aad(self):
        """Тест roundtrip без AAD."""
        etm = ETMMode(self.key_128)

        plaintext = b"Message without AAD"

        ciphertext = etm.encrypt(plaintext)  # AAD по умолчанию = b""
        decrypted = etm.decrypt(ciphertext)

        self.assertEqual(decrypted, plaintext)

    def test_file_roundtrip(self):
        """Тест: шифрование/дешифрование файла."""
        etm = ETMMode(self.key_128)

        input_file = Path(self.temp_dir) / "plain.txt"
        encrypted_file = Path(self.temp_dir) / "encrypted.bin"
        decrypted_file = Path(self.temp_dir) / "decrypted.txt"

        original = b"File content for ETM encryption test."
        aad = b"file metadata"

        with open(input_file, 'wb') as f:
            f.write(original)

        etm.encrypt_file(input_file, encrypted_file, aad)
        etm.decrypt_file(encrypted_file, decrypted_file, aad)

        with open(decrypted_file, 'rb') as f:
            result = f.read()

        self.assertEqual(result, original)

    # ==================== ФОРМАТ ВЫХОДА ====================

    def test_output_format(self):
        """Тест: правильный формат выхода (IV + ciphertext + tag)."""
        etm = ETMMode(self.key_128)

        plaintext = b"Test message"
        ciphertext = etm.encrypt(plaintext)

        # IV (16) + ciphertext (12) + tag (32) = 60 байт
        expected_len = etm.IV_SIZE + len(plaintext) + etm.TAG_SIZE
        self.assertEqual(len(ciphertext), expected_len)

    def test_different_ivs_different_output(self):
        """Тест: разные IV дают разный шифртекст."""
        plaintext = b"Same message"
        aad = b"same aad"

        etm1 = ETMMode(self.key_128)
        etm2 = ETMMode(self.key_128)

        ct1 = etm1.encrypt(plaintext, aad)
        ct2 = etm2.encrypt(plaintext, aad)

        # IV разные -> шифртексты разные
        self.assertNotEqual(ct1, ct2)

    # ==================== КЛЮЧИ И ДЕРИВАЦИЯ ====================

    def test_key_derivation(self):
        """Тест: деривация ключей из мастер-ключа."""
        etm = ETMMode(self.key_128)

        # Проверяем что ключи деривированы
        self.assertEqual(len(etm.enc_key), 16)  # AES-128 ключ
        self.assertEqual(len(etm.mac_key), 32)  # HMAC-SHA256 ключ

        # Ключи должны отличаться от мастер-ключа
        self.assertNotEqual(etm.enc_key, self.key_128[:16])

    def test_different_key_sizes(self):
        """Тест: поддержка разных размеров ключей."""
        for key in [self.key_128, self.key_256]:
            with self.subTest(key_len=len(key)):
                etm = ETMMode(key)

                plaintext = b"Test message"
                ciphertext = etm.encrypt(plaintext)
                decrypted = etm.decrypt(ciphertext)

                self.assertEqual(decrypted, plaintext)

    def test_invalid_key_size(self):
        """Тест: неверный размер ключа."""
        with self.assertRaises(ValueError):
            ETMMode(b"short")  # < 16 байт

    # ==================== АУТЕНТИФИКАЦИЯ ====================

    def test_authentication_with_aad(self):
        """Тест: AAD включается в аутентификацию."""
        etm = ETMMode(self.key_128)

        plaintext = b"Message"
        aad1 = b"aad version 1"
        aad2 = b"aad version 2"

        ciphertext = etm.encrypt(plaintext, aad1)

        # Дешифрование с правильным AAD - успех
        decrypted = etm.decrypt(ciphertext, aad1)
        self.assertEqual(decrypted, plaintext)

        # Дешифрование с неверным AAD - ошибка
        with self.assertRaises(AuthenticationError):
            etm.decrypt(ciphertext, aad2)

    # ==================== НЕГАТИВНЫЕ ТЕСТЫ ====================

    def test_tampered_ciphertext_fails(self):
        """Тест: изменённый шифртекст не проходит аутентификацию."""
        etm = ETMMode(self.key_128)

        plaintext = b"Secret message"
        ciphertext = bytearray(etm.encrypt(plaintext))

        # Портим байт в середине (в шифртексте)
        ciphertext[20] ^= 0x01

        with self.assertRaises(AuthenticationError):
            etm.decrypt(bytes(ciphertext))

    def test_tampered_tag_fails(self):
        """Тест: изменённый тег не проходит аутентификацию."""
        etm = ETMMode(self.key_128)

        plaintext = b"Secret message"
        ciphertext = bytearray(etm.encrypt(plaintext))

        # Портим последний байт (тег)
        ciphertext[-1] ^= 0x01

        with self.assertRaises(AuthenticationError):
            etm.decrypt(bytes(ciphertext))


    def test_wrong_aad_fails(self):
        """Тест: неверный AAD не проходит аутентификацию."""
        etm = ETMMode(self.key_128)

        plaintext = b"Secret message"
        aad = b"correct aad"

        ciphertext = etm.encrypt(plaintext, aad)

        with self.assertRaises(AuthenticationError):
            etm.decrypt(ciphertext, b"wrong aad")

    def test_truncated_data_fails(self):
        """Тест: обрезанные данные."""
        etm = ETMMode(self.key_128)

        plaintext = b"Secret message"
        ciphertext = etm.encrypt(plaintext)

        # Обрезаем данные
        truncated = ciphertext[:20]

        with self.assertRaises(ValueError):
            etm.decrypt(truncated)

    def test_file_not_found(self):
        """Тест: несуществующий файл."""
        etm = ETMMode(self.key_128)

        with self.assertRaises(CryptoOperationError):
            etm.encrypt_file("/nonexistent/file.txt", Path(self.temp_dir) / "out.bin")

    def test_file_auth_failure_deletes_output(self):
        """Тест: при ошибке аутентификации выходной файл удаляется."""
        etm = ETMMode(self.key_128)

        input_file = Path(self.temp_dir) / "plain.txt"
        encrypted_file = Path(self.temp_dir) / "enc.bin"
        decrypted_file = Path(self.temp_dir) / "dec.txt"

        with open(input_file, 'wb') as f:
            f.write(b"Test message")

        etm.encrypt_file(input_file, encrypted_file, aad=b"correct")

        # Пытаемся дешифровать с неверным AAD
        with self.assertRaises(AuthenticationError):
            etm.decrypt_file(encrypted_file, decrypted_file, aad=b"wrong")

        # Выходной файл не должен существовать
        self.assertFalse(decrypted_file.exists())

    def test_constant_time_compare(self):
        """Тест: функция сравнения за константное время."""
        # Одинаковые
        self.assertTrue(ETMMode._constant_time_compare(b"test", b"test"))

        # Разные
        self.assertFalse(ETMMode._constant_time_compare(b"test", b"Test"))

        # Разная длина
        self.assertFalse(ETMMode._constant_time_compare(b"test", b"testing"))


if __name__ == '__main__':
    unittest.main(verbosity=2)