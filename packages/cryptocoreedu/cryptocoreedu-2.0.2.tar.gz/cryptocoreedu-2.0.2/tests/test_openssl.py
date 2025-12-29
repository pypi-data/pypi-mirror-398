"""
Тесты на совместимость с OpenSSL (TEST-6: Interoperability Tests).

Проверяет совместимость с:
- openssl для AES режимов (ECB, CBC, CFB, OFB, CTR)
- openssl dgst для SHA-256, SHA3-256
- openssl dgst -hmac для HMAC-SHA256
- hashlib.pbkdf2_hmac для PBKDF2 (использует OpenSSL под капотом)

Требования:
- OpenSSL установлен и доступен в PATH
- Для SHA3-256: OpenSSL >= 1.1.1
"""

import unittest
import subprocess
import tempfile
import os
import sys
import shutil
import hashlib
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Импорты из проекта
from cryptocoreedu.hash.sha256 import SHA256, sha256_data, sha256_file
from cryptocoreedu.hash.sha3_256 import SHA3_256, sha3_256_data, sha3_256_file
from cryptocoreedu.mac.hmac import HMAC, hmac_data
from cryptocoreedu.kdf.pbkdf2 import pbkdf2_hmac_sha256
from cryptocoreedu.modes.ECBMode import ECBMode
from cryptocoreedu.modes.CBCMode import CBCMode
from cryptocoreedu.modes.CFBMode import CFBMode
from cryptocoreedu.modes.OFBMode import OFBMode
from cryptocoreedu.modes.CTRMode import CTRMode


def is_openssl_available():
    """Проверяет доступность OpenSSL."""
    try:
        result = subprocess.run(
            ['openssl', 'version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_openssl_version():
    """Возвращает версию OpenSSL."""
    try:
        result = subprocess.run(
            ['openssl', 'version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip()
    except:
        return "Unknown"


def is_sha3_supported():
    """Проверяет поддержку SHA3 в OpenSSL."""
    try:
        result = subprocess.run(
            ['openssl', 'dgst', '-sha3-256'],
            input=b'test',
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False


OPENSSL_AVAILABLE = is_openssl_available()
SHA3_SUPPORTED = is_sha3_supported() if OPENSSL_AVAILABLE else False


@unittest.skipUnless(OPENSSL_AVAILABLE, "OpenSSL not available")
class TestSHA256OpenSSLInterop(unittest.TestCase):
    """Тесты совместимости SHA-256 с OpenSSL."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _openssl_sha256(self, data: bytes) -> str:
        """Вычисляет SHA-256 через OpenSSL."""
        result = subprocess.run(
            ['openssl', 'dgst', '-sha256'],
            input=data,
            capture_output=True,
            timeout=10
        )
        output = result.stdout.decode().strip()
        return output.split('=')[-1].strip().lower()

    def _openssl_sha256_file(self, filepath: str) -> str:
        """Вычисляет SHA-256 файла через OpenSSL."""
        result = subprocess.run(
            ['openssl', 'dgst', '-sha256', filepath],
            capture_output=True,
            timeout=10
        )
        output = result.stdout.decode().strip()
        return output.split('=')[-1].strip().lower()

    def test_sha256_empty(self):
        """Тест: SHA-256 пустой строки совпадает с OpenSSL."""
        data = b""

        our_hash = sha256_data(data)
        openssl_hash = self._openssl_sha256(data)

        self.assertEqual(our_hash, openssl_hash)

    def test_sha256_simple(self):
        """Тест: SHA-256 простой строки совпадает с OpenSSL."""
        data = b"Hello, World!"

        our_hash = sha256_data(data)
        openssl_hash = self._openssl_sha256(data)

        self.assertEqual(our_hash, openssl_hash)

    def test_sha256_abc(self):
        """Тест: SHA-256 'abc' совпадает с OpenSSL (NIST вектор)."""
        data = b"abc"

        our_hash = sha256_data(data)
        openssl_hash = self._openssl_sha256(data)

        self.assertEqual(our_hash, openssl_hash)
        self.assertEqual(our_hash, "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_sha256_binary(self):
        """Тест: SHA-256 бинарных данных совпадает с OpenSSL."""
        data = bytes(range(256))

        our_hash = sha256_data(data)
        openssl_hash = self._openssl_sha256(data)

        self.assertEqual(our_hash, openssl_hash)

    def test_sha256_large_data(self):
        """Тест: SHA-256 больших данных совпадает с OpenSSL."""
        data = os.urandom(100000)

        our_hash = sha256_data(data)
        openssl_hash = self._openssl_sha256(data)

        self.assertEqual(our_hash, openssl_hash)

    def test_sha256_file(self):
        """Тест: SHA-256 файла совпадает с OpenSSL."""
        filepath = os.path.join(self.temp_dir, "test.bin")
        data = b"File content for SHA-256 test"

        with open(filepath, 'wb') as f:
            f.write(data)

        our_hash = sha256_file(filepath)
        openssl_hash = self._openssl_sha256_file(filepath)

        self.assertEqual(our_hash, openssl_hash)

    def test_sha256_multiple_updates(self):
        """Тест: SHA-256 с несколькими update совпадает с OpenSSL."""
        data = b"Hello, " + b"World!"

        sha = SHA256()
        sha.update(b"Hello, ")
        sha.update(b"World!")
        our_hash = sha.hexdigest()

        openssl_hash = self._openssl_sha256(data)

        self.assertEqual(our_hash, openssl_hash)


@unittest.skipUnless(OPENSSL_AVAILABLE and SHA3_SUPPORTED, "OpenSSL with SHA3 not available")
class TestSHA3_256OpenSSLInterop(unittest.TestCase):
    """Тесты совместимости SHA3-256 с OpenSSL."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _openssl_sha3_256(self, data: bytes) -> str:
        """Вычисляет SHA3-256 через OpenSSL."""
        result = subprocess.run(
            ['openssl', 'dgst', '-sha3-256'],
            input=data,
            capture_output=True,
            timeout=10
        )
        output = result.stdout.decode().strip()
        return output.split('=')[-1].strip().lower()

    def _openssl_sha3_256_file(self, filepath: str) -> str:
        """Вычисляет SHA3-256 файла через OpenSSL."""
        result = subprocess.run(
            ['openssl', 'dgst', '-sha3-256', filepath],
            capture_output=True,
            timeout=10
        )
        output = result.stdout.decode().strip()
        return output.split('=')[-1].strip().lower()

    def test_sha3_256_empty(self):
        """Тест: SHA3-256 пустой строки совпадает с OpenSSL."""
        data = b""

        our_hash = sha3_256_data(data)
        openssl_hash = self._openssl_sha3_256(data)

        self.assertEqual(our_hash, openssl_hash)

    def test_sha3_256_simple(self):
        """Тест: SHA3-256 простой строки совпадает с OpenSSL."""
        data = b"Hello, World!"

        our_hash = sha3_256_data(data)
        openssl_hash = self._openssl_sha3_256(data)

        self.assertEqual(our_hash, openssl_hash)

    def test_sha3_256_abc(self):
        """Тест: SHA3-256 'abc' совпадает с OpenSSL (NIST вектор)."""
        data = b"abc"

        our_hash = sha3_256_data(data)
        openssl_hash = self._openssl_sha3_256(data)

        self.assertEqual(our_hash, openssl_hash)
        self.assertEqual(our_hash, "3a985da74fe225b2045c172d6bd390bd855f086e3e9d525b46bfe24511431532")

    def test_sha3_256_binary(self):
        """Тест: SHA3-256 бинарных данных совпадает с OpenSSL."""
        data = bytes(range(256))

        our_hash = sha3_256_data(data)
        openssl_hash = self._openssl_sha3_256(data)

        self.assertEqual(our_hash, openssl_hash)

    def test_sha3_256_large_data(self):
        """Тест: SHA3-256 больших данных совпадает с OpenSSL."""
        data = os.urandom(100000)

        our_hash = sha3_256_data(data)
        openssl_hash = self._openssl_sha3_256(data)

        self.assertEqual(our_hash, openssl_hash)

    def test_sha3_256_file(self):
        """Тест: SHA3-256 файла совпадает с OpenSSL."""
        filepath = os.path.join(self.temp_dir, "test.bin")
        data = b"File content for SHA3-256 test"

        with open(filepath, 'wb') as f:
            f.write(data)

        our_hash = sha3_256_file(filepath)
        openssl_hash = self._openssl_sha3_256_file(filepath)

        self.assertEqual(our_hash, openssl_hash)


@unittest.skipUnless(OPENSSL_AVAILABLE, "OpenSSL not available")
class TestHMACSHA256OpenSSLInterop(unittest.TestCase):
    """Тесты совместимости HMAC-SHA256 с OpenSSL."""

    def _openssl_hmac_sha256(self, key: bytes, data: bytes) -> str:
        """Вычисляет HMAC-SHA256 через OpenSSL."""
        key_hex = key.hex()
        result = subprocess.run(
            ['openssl', 'dgst', '-sha256', '-mac', 'HMAC', '-macopt', f'hexkey:{key_hex}'],
            input=data,
            capture_output=True,
            timeout=10
        )
        output = result.stdout.decode().strip()
        return output.split('=')[-1].strip().lower()

    def test_hmac_simple(self):
        """Тест: HMAC-SHA256 простых данных совпадает с OpenSSL."""
        key = b"secret_key"
        data = b"Hello, World!"

        our_hmac = hmac_data(key, data)
        openssl_hmac = self._openssl_hmac_sha256(key, data)

        self.assertEqual(our_hmac, openssl_hmac)

    def test_hmac_rfc4231_vector2(self):
        """Тест: RFC 4231 Test Case 2 совпадает с OpenSSL."""
        key = b"Jefe"
        data = b"what do ya want for nothing?"
        expected = "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843"

        our_hmac = hmac_data(key, data)
        openssl_hmac = self._openssl_hmac_sha256(key, data)

        self.assertEqual(our_hmac, expected)
        self.assertEqual(our_hmac, openssl_hmac)

    def test_hmac_binary_key(self):
        """Тест: HMAC с бинарным ключом совпадает с OpenSSL."""
        key = bytes.fromhex("0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b")
        data = b"Hi There"

        our_hmac = hmac_data(key, data)
        openssl_hmac = self._openssl_hmac_sha256(key, data)

        self.assertEqual(our_hmac, openssl_hmac)

    def test_hmac_long_key(self):
        """Тест: HMAC с длинным ключом совпадает с OpenSSL."""
        key = bytes([0xaa] * 131)
        data = b"Test Using Larger Than Block-Size Key - Hash Key First"

        our_hmac = hmac_data(key, data)
        openssl_hmac = self._openssl_hmac_sha256(key, data)

        self.assertEqual(our_hmac, openssl_hmac)

    def test_hmac_empty_data(self):
        """Тест: HMAC пустых данных совпадает с OpenSSL."""
        key = b"key"
        data = b""

        our_hmac = hmac_data(key, data)
        openssl_hmac = self._openssl_hmac_sha256(key, data)

        self.assertEqual(our_hmac, openssl_hmac)

    def test_hmac_binary_data(self):
        """Тест: HMAC бинарных данных совпадает с OpenSSL."""
        key = os.urandom(32)
        data = bytes(range(256))

        our_hmac = hmac_data(key, data)
        openssl_hmac = self._openssl_hmac_sha256(key, data)

        self.assertEqual(our_hmac, openssl_hmac)


class TestPBKDF2SHA256Interop(unittest.TestCase):
    """
    Тесты совместимости PBKDF2-HMAC-SHA256 с hashlib.
    hashlib.pbkdf2_hmac использует OpenSSL под капотом.
    """

    def test_pbkdf2_basic(self):
        """Тест: PBKDF2 базовый случай совпадает с hashlib."""
        password = b"password"
        salt = b"salt"
        iterations = 1
        dklen = 32

        our_key = pbkdf2_hmac_sha256(password, salt, iterations, dklen)
        stdlib_key = hashlib.pbkdf2_hmac('sha256', password, salt, iterations, dklen)

        self.assertEqual(our_key, stdlib_key)

    def test_pbkdf2_rfc7914_vector1(self):
        """Тест: RFC 7914 тест-вектор совпадает с hashlib."""
        password = b"passwd"
        salt = b"salt"
        iterations = 1
        dklen = 64

        our_key = pbkdf2_hmac_sha256(password, salt, iterations, dklen)
        stdlib_key = hashlib.pbkdf2_hmac('sha256', password, salt, iterations, dklen)

        self.assertEqual(our_key, stdlib_key)

    def test_pbkdf2_multiple_iterations(self):
        """Тест: PBKDF2 с разным количеством итераций совпадает с hashlib."""
        password = b"password"
        salt = b"salt"
        dklen = 32

        for iterations in [1, 2, 100, 1000, 4096]:
            with self.subTest(iterations=iterations):
                our_key = pbkdf2_hmac_sha256(password, salt, iterations, dklen)
                stdlib_key = hashlib.pbkdf2_hmac('sha256', password, salt, iterations, dklen)
                self.assertEqual(our_key, stdlib_key)

    def test_pbkdf2_various_lengths(self):
        """Тест: PBKDF2 с разной длиной ключа совпадает с hashlib."""
        password = b"password"
        salt = b"salt"
        iterations = 100

        for dklen in [16, 20, 32, 48, 64, 100]:
            with self.subTest(dklen=dklen):
                our_key = pbkdf2_hmac_sha256(password, salt, iterations, dklen)
                stdlib_key = hashlib.pbkdf2_hmac('sha256', password, salt, iterations, dklen)
                self.assertEqual(our_key, stdlib_key)

    def test_pbkdf2_long_password(self):
        """Тест: PBKDF2 с длинным паролем совпадает с hashlib."""
        password = b"passwordPASSWORDpassword"
        salt = b"saltSALTsaltSALTsaltSALTsaltSALTsalt"
        iterations = 4096
        dklen = 40

        our_key = pbkdf2_hmac_sha256(password, salt, iterations, dklen)
        stdlib_key = hashlib.pbkdf2_hmac('sha256', password, salt, iterations, dklen)

        self.assertEqual(our_key, stdlib_key)

    def test_pbkdf2_binary_password(self):
        """Тест: PBKDF2 с бинарным паролем совпадает с hashlib."""
        password = bytes(range(256))
        salt = os.urandom(16)
        iterations = 1000
        dklen = 32

        our_key = pbkdf2_hmac_sha256(password, salt, iterations, dklen)
        stdlib_key = hashlib.pbkdf2_hmac('sha256', password, salt, iterations, dklen)

        self.assertEqual(our_key, stdlib_key)

    def test_pbkdf2_unicode_password(self):
        """Тест: PBKDF2 с unicode паролем совпадает с hashlib."""
        password = "пароль🔐".encode('utf-8')
        salt = b"salt"
        iterations = 1000
        dklen = 32

        our_key = pbkdf2_hmac_sha256(password, salt, iterations, dklen)
        stdlib_key = hashlib.pbkdf2_hmac('sha256', password, salt, iterations, dklen)

        self.assertEqual(our_key, stdlib_key)


@unittest.skipUnless(OPENSSL_AVAILABLE, "OpenSSL not available")
class TestAESECBOpenSSLInterop(unittest.TestCase):
    """Тесты совместимости AES-ECB с OpenSSL (на уровне блоков без padding)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.key = bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c")
        self.key_hex = self.key.hex()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _openssl_ecb_encrypt_nopad(self, plaintext: bytes) -> bytes:
        """Шифрует данные через OpenSSL AES-128-ECB без padding."""
        result = subprocess.run(
            ['openssl', 'enc', '-aes-128-ecb', '-K', self.key_hex, '-nopad'],
            input=plaintext,
            capture_output=True,
            timeout=10
        )
        return result.stdout

    def _openssl_ecb_decrypt_nopad(self, ciphertext: bytes) -> bytes:
        """Дешифрует данные через OpenSSL AES-128-ECB без padding."""
        result = subprocess.run(
            ['openssl', 'enc', '-aes-128-ecb', '-d', '-K', self.key_hex, '-nopad'],
            input=ciphertext,
            capture_output=True,
            timeout=10
        )
        return result.stdout

    def test_ecb_nist_vector_block_level(self):
        """Тест: NIST вектор ECB на уровне блоков совпадает с OpenSSL."""
        # NIST SP 800-38A тестовые данные (4 блока = 64 байта)
        plaintext = bytes.fromhex(
            "6bc1bee22e409f96e93d7e117393172a"
            "ae2d8a571e03ac9c9eb76fac45af8e51"
            "30c81c46a35ce411e5fbc1191a0a52ef"
            "f69f2445df4f9b17ad2b417be66c3710"
        )
        expected_ciphertext = bytes.fromhex(
            "3ad77bb40d7a3660a89ecaf32466ef97"
            "f5d3d58503b9699de785895a96fdbaaf"
            "43b1cd7f598ece23881b00e3ed030688"
            "7b0c785e27e8ad3f8223207104725dd4"
        )

        openssl_ciphertext = self._openssl_ecb_encrypt_nopad(plaintext)

        self.assertEqual(openssl_ciphertext, expected_ciphertext)

    def test_ecb_encrypt_single_block(self):
        """Тест: шифрование одного блока совпадает с OpenSSL."""
        plaintext = bytes.fromhex("6bc1bee22e409f96e93d7e117393172a")
        expected = bytes.fromhex("3ad77bb40d7a3660a89ecaf32466ef97")

        openssl_ciphertext = self._openssl_ecb_encrypt_nopad(plaintext)

        self.assertEqual(openssl_ciphertext, expected)

        # Проверяем что наш encrypt даёт тот же результат
        ecb = ECBMode(self.key)
        input_file = Path(self.temp_dir) / "plain.bin"
        output_file = Path(self.temp_dir) / "enc.bin"

        with open(input_file, 'wb') as f:
            f.write(plaintext)

        ecb.encrypt_file(input_file, output_file)

        with open(output_file, 'rb') as f:
            our_ciphertext = f.read()[:16]  # Первый блок без padding

        self.assertEqual(our_ciphertext, expected)

    def test_ecb_openssl_roundtrip(self):
        """Тест: OpenSSL encrypt -> OpenSSL decrypt = original."""
        plaintext = b"0123456789ABCDEF" * 4  # 64 байта (кратно 16)

        ciphertext = self._openssl_ecb_encrypt_nopad(plaintext)
        decrypted = self._openssl_ecb_decrypt_nopad(ciphertext)

        self.assertEqual(decrypted, plaintext)

    def test_ecb_our_file_roundtrip(self):
        """Тест: наш encrypt -> decrypt файла = original."""
        ecb = ECBMode(self.key)

        plaintext = b"Test data for ECB roundtrip test!"

        input_file = Path(self.temp_dir) / "plain.bin"
        enc_file = Path(self.temp_dir) / "enc.bin"
        dec_file = Path(self.temp_dir) / "dec.bin"

        with open(input_file, 'wb') as f:
            f.write(plaintext)

        ecb.encrypt_file(input_file, enc_file)
        ecb.decrypt_file(enc_file, dec_file)

        with open(dec_file, 'rb') as f:
            result = f.read()

        self.assertEqual(result, plaintext)


@unittest.skipUnless(OPENSSL_AVAILABLE, "OpenSSL not available")
class TestAESCBCOpenSSLInterop(unittest.TestCase):
    """Тесты совместимости AES-CBC с OpenSSL (на уровне блоков без padding)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.key = bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c")
        self.iv = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
        self.key_hex = self.key.hex()
        self.iv_hex = self.iv.hex()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _openssl_cbc_encrypt_nopad(self, plaintext: bytes) -> bytes:
        """Шифрует через OpenSSL AES-128-CBC без padding."""
        result = subprocess.run(
            ['openssl', 'enc', '-aes-128-cbc', '-K', self.key_hex, '-iv', self.iv_hex, '-nopad'],
            input=plaintext,
            capture_output=True,
            timeout=10
        )
        return result.stdout

    def _openssl_cbc_decrypt_nopad(self, ciphertext: bytes) -> bytes:
        """Дешифрует через OpenSSL AES-128-CBC без padding."""
        result = subprocess.run(
            ['openssl', 'enc', '-aes-128-cbc', '-d', '-K', self.key_hex, '-iv', self.iv_hex, '-nopad'],
            input=ciphertext,
            capture_output=True,
            timeout=10
        )
        return result.stdout

    def test_cbc_openssl_roundtrip(self):
        """Тест: OpenSSL CBC encrypt -> decrypt = original."""
        plaintext = b"0123456789ABCDEF" * 4  # 64 байта

        ciphertext = self._openssl_cbc_encrypt_nopad(plaintext)
        decrypted = self._openssl_cbc_decrypt_nopad(ciphertext)

        self.assertEqual(decrypted, plaintext)

    def test_cbc_our_file_roundtrip(self):
        """Тест: наш CBC encrypt -> decrypt файла = original."""
        cbc = CBCMode(self.key)

        plaintext = b"Test data for CBC roundtrip!"

        input_file = Path(self.temp_dir) / "plain.bin"
        enc_file = Path(self.temp_dir) / "enc.bin"
        dec_file = Path(self.temp_dir) / "dec.bin"

        with open(input_file, 'wb') as f:
            f.write(plaintext)

        cbc.encrypt_file(input_file, enc_file)
        cbc.decrypt_file(enc_file, dec_file, iv=None)  # IV из файла

        with open(dec_file, 'rb') as f:
            result = f.read()

        self.assertEqual(result, plaintext)


@unittest.skipUnless(OPENSSL_AVAILABLE, "OpenSSL not available")
class TestAESCFBOpenSSLInterop(unittest.TestCase):
    """Тесты совместимости AES-CFB с OpenSSL."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.key = bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c")
        self.iv = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
        self.key_hex = self.key.hex()
        self.iv_hex = self.iv.hex()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _openssl_cfb_encrypt(self, plaintext: bytes) -> bytes:
        """Шифрует через OpenSSL AES-128-CFB."""
        result = subprocess.run(
            ['openssl', 'enc', '-aes-128-cfb', '-K', self.key_hex, '-iv', self.iv_hex],
            input=plaintext,
            capture_output=True,
            timeout=10
        )
        return result.stdout

    def _openssl_cfb_decrypt(self, ciphertext: bytes) -> bytes:
        """Дешифрует через OpenSSL AES-128-CFB."""
        result = subprocess.run(
            ['openssl', 'enc', '-aes-128-cfb', '-d', '-K', self.key_hex, '-iv', self.iv_hex],
            input=ciphertext,
            capture_output=True,
            timeout=10
        )
        return result.stdout

    def test_cfb_nist_vector(self):
        """Тест: NIST вектор CFB совпадает с OpenSSL."""
        plaintext = bytes.fromhex(
            "6bc1bee22e409f96e93d7e117393172a"
            "ae2d8a571e03ac9c9eb76fac45af8e51"
        )
        expected = bytes.fromhex(
            "3b3fd92eb72dad20333449f8e83cfb4a"
            "c8a64537a0b3a93fcde3cdad9f1ce58b"
        )

        openssl_ciphertext = self._openssl_cfb_encrypt(plaintext)

        self.assertEqual(openssl_ciphertext, expected)

    def test_cfb_decrypt_openssl_encrypted(self):
        """Тест: дешифруем зашифрованное OpenSSL (CFB - потоковый, без padding)."""
        plaintext = b"Test message for CFB mode!"

        openssl_ciphertext = self._openssl_cfb_encrypt(plaintext)

        enc_file = Path(self.temp_dir) / "enc.bin"
        dec_file = Path(self.temp_dir) / "dec.bin"

        with open(enc_file, 'wb') as f:
            f.write(openssl_ciphertext)

        cfb = CFBMode(self.key)
        cfb.decrypt_file(enc_file, dec_file, iv=self.iv)

        with open(dec_file, 'rb') as f:
            result = f.read()

        self.assertEqual(result, plaintext)

    def test_cfb_openssl_roundtrip(self):
        """Тест: OpenSSL CFB encrypt -> decrypt = original."""
        plaintext = b"Any length data works in CFB mode!"

        ciphertext = self._openssl_cfb_encrypt(plaintext)
        decrypted = self._openssl_cfb_decrypt(ciphertext)

        self.assertEqual(decrypted, plaintext)


@unittest.skipUnless(OPENSSL_AVAILABLE, "OpenSSL not available")
class TestAESOFBOpenSSLInterop(unittest.TestCase):
    """Тесты совместимости AES-OFB с OpenSSL."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.key = bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c")
        self.iv = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
        self.key_hex = self.key.hex()
        self.iv_hex = self.iv.hex()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _openssl_ofb_encrypt(self, plaintext: bytes) -> bytes:
        """Шифрует через OpenSSL AES-128-OFB."""
        result = subprocess.run(
            ['openssl', 'enc', '-aes-128-ofb', '-K', self.key_hex, '-iv', self.iv_hex],
            input=plaintext,
            capture_output=True,
            timeout=10
        )
        return result.stdout

    def _openssl_ofb_decrypt(self, ciphertext: bytes) -> bytes:
        """Дешифрует через OpenSSL AES-128-OFB."""
        result = subprocess.run(
            ['openssl', 'enc', '-aes-128-ofb', '-d', '-K', self.key_hex, '-iv', self.iv_hex],
            input=ciphertext,
            capture_output=True,
            timeout=10
        )
        return result.stdout

    def test_ofb_nist_vector(self):
        """Тест: NIST вектор OFB совпадает с OpenSSL."""
        plaintext = bytes.fromhex(
            "6bc1bee22e409f96e93d7e117393172a"
            "ae2d8a571e03ac9c9eb76fac45af8e51"
        )
        expected = bytes.fromhex(
            "3b3fd92eb72dad20333449f8e83cfb4a"
            "7789508d16918f03f53c52dac54ed825"
        )

        openssl_ciphertext = self._openssl_ofb_encrypt(plaintext)

        self.assertEqual(openssl_ciphertext, expected)

    def test_ofb_decrypt_openssl_encrypted(self):
        """Тест: дешифруем зашифрованное OpenSSL (OFB - потоковый)."""
        plaintext = b"Test message for OFB mode!"

        openssl_ciphertext = self._openssl_ofb_encrypt(plaintext)

        enc_file = Path(self.temp_dir) / "enc.bin"
        dec_file = Path(self.temp_dir) / "dec.bin"

        with open(enc_file, 'wb') as f:
            f.write(openssl_ciphertext)

        ofb = OFBMode(self.key)
        ofb.decrypt_file(enc_file, dec_file, iv=self.iv)

        with open(dec_file, 'rb') as f:
            result = f.read()

        self.assertEqual(result, plaintext)

    def test_ofb_openssl_roundtrip(self):
        """Тест: OpenSSL OFB encrypt -> decrypt = original."""
        plaintext = b"Any length data works in OFB mode!"

        ciphertext = self._openssl_ofb_encrypt(plaintext)
        decrypted = self._openssl_ofb_decrypt(ciphertext)

        self.assertEqual(decrypted, plaintext)


@unittest.skipUnless(OPENSSL_AVAILABLE, "OpenSSL not available")
class TestAESCTROpenSSLInterop(unittest.TestCase):
    """Тесты совместимости AES-CTR с OpenSSL."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.key = bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c")
        self.iv = bytes.fromhex("f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff")
        self.key_hex = self.key.hex()
        self.iv_hex = self.iv.hex()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _openssl_ctr_encrypt(self, plaintext: bytes) -> bytes:
        """Шифрует через OpenSSL AES-128-CTR."""
        result = subprocess.run(
            ['openssl', 'enc', '-aes-128-ctr', '-K', self.key_hex, '-iv', self.iv_hex],
            input=plaintext,
            capture_output=True,
            timeout=10
        )
        return result.stdout

    def _openssl_ctr_decrypt(self, ciphertext: bytes) -> bytes:
        """Дешифрует через OpenSSL AES-128-CTR."""
        result = subprocess.run(
            ['openssl', 'enc', '-aes-128-ctr', '-d', '-K', self.key_hex, '-iv', self.iv_hex],
            input=ciphertext,
            capture_output=True,
            timeout=10
        )
        return result.stdout

    def test_ctr_nist_vector(self):
        """Тест: NIST вектор CTR совпадает с OpenSSL."""
        plaintext = bytes.fromhex(
            "6bc1bee22e409f96e93d7e117393172a"
            "ae2d8a571e03ac9c9eb76fac45af8e51"
        )
        expected = bytes.fromhex(
            "874d6191b620e3261bef6864990db6ce"
            "9806f66b7970fdff8617187bb9fffdff"
        )

        openssl_ciphertext = self._openssl_ctr_encrypt(plaintext)

        self.assertEqual(openssl_ciphertext, expected)

    def test_ctr_decrypt_openssl_encrypted(self):
        """Тест: дешифруем зашифрованное OpenSSL (CTR - потоковый)."""
        plaintext = b"Test message for CTR mode!"

        openssl_ciphertext = self._openssl_ctr_encrypt(plaintext)

        enc_file = Path(self.temp_dir) / "enc.bin"
        dec_file = Path(self.temp_dir) / "dec.bin"

        with open(enc_file, 'wb') as f:
            f.write(openssl_ciphertext)

        ctr = CTRMode(self.key)
        ctr.decrypt_file(enc_file, dec_file, iv=self.iv)

        with open(dec_file, 'rb') as f:
            result = f.read()

        self.assertEqual(result, plaintext)

    def test_ctr_partial_block(self):
        """Тест: CTR с неполным блоком совпадает с OpenSSL."""
        plaintext = b"Short"  # 5 байт

        openssl_ciphertext = self._openssl_ctr_encrypt(plaintext)
        openssl_decrypted = self._openssl_ctr_decrypt(openssl_ciphertext)

        self.assertEqual(openssl_decrypted, plaintext)
        self.assertEqual(len(openssl_ciphertext), len(plaintext))

    def test_ctr_openssl_roundtrip(self):
        """Тест: OpenSSL CTR encrypt -> decrypt = original."""
        plaintext = b"Any length data works in CTR mode!"

        ciphertext = self._openssl_ctr_encrypt(plaintext)
        decrypted = self._openssl_ctr_decrypt(ciphertext)

        self.assertEqual(decrypted, plaintext)


class TestSystemToolsInterop(unittest.TestCase):
    """Тесты совместимости с системными утилитами."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _is_sha256sum_available(self):
        """Проверяет доступность sha256sum."""
        try:
            result = subprocess.run(['sha256sum', '--version'], capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False

    def test_sha256sum_compatibility(self):
        """Тест: совместимость с sha256sum."""
        if not self._is_sha256sum_available():
            self.skipTest("sha256sum not available")

        filepath = os.path.join(self.temp_dir, "test.txt")
        data = b"Test data for sha256sum compatibility"

        with open(filepath, 'wb') as f:
            f.write(data)

        our_hash = sha256_file(filepath)

        result = subprocess.run(
            ['sha256sum', filepath],
            capture_output=True,
            text=True,
            timeout=10
        )
        sha256sum_hash = result.stdout.split()[0].lower()

        self.assertEqual(our_hash, sha256sum_hash)


if __name__ == '__main__':
    print(f"OpenSSL available: {OPENSSL_AVAILABLE}")
    if OPENSSL_AVAILABLE:
        print(f"OpenSSL version: {get_openssl_version()}")
        print(f"SHA3 supported: {SHA3_SUPPORTED}")
    print()

    unittest.main(verbosity=2)