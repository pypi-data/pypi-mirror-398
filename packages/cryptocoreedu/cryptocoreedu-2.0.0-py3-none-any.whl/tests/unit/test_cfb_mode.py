"""
Unit tests for AES CFB Mode implementation.
Tests include NIST SP 800-38A test vectors and negative scenarios.
Reference: https://csrc.nist.gov/publications/detail/sp/800-38a/final
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from cryptocoreedu.modes.CFBMode import CFBMode
from cryptocoreedu.exceptions import CryptoOperationError


class TestCFBModeBasic(unittest.TestCase):
    """Basic functionality tests for CFBMode class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.key = bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c")

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """Test CFBMode initialization."""
        cfb = CFBMode(self.key)
        self.assertEqual(cfb.key, self.key)
        self.assertEqual(cfb.BLOCK_SIZE, 16)

    def test_encrypt_decrypt_roundtrip(self):
        """Test that encrypt followed by decrypt returns original data."""
        cfb = CFBMode(self.key)

        input_file = Path(self.temp_dir) / "plaintext.bin"
        encrypted_file = Path(self.temp_dir) / "encrypted.bin"
        decrypted_file = Path(self.temp_dir) / "decrypted.bin"

        original_data = b"Hello, World! This is a test message for CFB mode."
        with open(input_file, 'wb') as f:
            f.write(original_data)

        cfb.encrypt_file(input_file, encrypted_file)
        cfb.decrypt_file(encrypted_file, decrypted_file, iv=None)

        with open(decrypted_file, 'rb') as f:
            decrypted_data = f.read()

        self.assertEqual(decrypted_data, original_data)

    def test_stream_cipher_property(self):
        """Test that CFB produces ciphertext of same length as plaintext."""
        cfb = CFBMode(self.key)

        input_file = Path(self.temp_dir) / "plaintext.bin"
        encrypted_file = Path(self.temp_dir) / "encrypted.bin"

        # Use non-block-aligned data to verify no padding
        original_data = b"12345"  # 5 bytes (not a multiple of 16)
        with open(input_file, 'wb') as f:
            f.write(original_data)

        cfb.encrypt_file(input_file, encrypted_file)

        with open(encrypted_file, 'rb') as f:
            encrypted_data = f.read()

        # Encrypted data = IV (16) + ciphertext (same as plaintext length)
        expected_length = 16 + len(original_data)
        self.assertEqual(len(encrypted_data), expected_length)

    def test_different_ivs_produce_different_ciphertext(self):
        """Test that different IVs produce different ciphertext."""
        cfb = CFBMode(self.key)

        input_file = Path(self.temp_dir) / "plaintext.bin"
        encrypted_file1 = Path(self.temp_dir) / "encrypted1.bin"
        encrypted_file2 = Path(self.temp_dir) / "encrypted2.bin"

        with open(input_file, 'wb') as f:
            f.write(b"Same plaintext data")

        cfb.encrypt_file(input_file, encrypted_file1)
        cfb.encrypt_file(input_file, encrypted_file2)

        with open(encrypted_file1, 'rb') as f:
            ciphertext1 = f.read()
        with open(encrypted_file2, 'rb') as f:
            ciphertext2 = f.read()

        self.assertNotEqual(ciphertext1, ciphertext2)


class TestCFBModeNISTVectors(unittest.TestCase):
    """
    Known-Answer Tests (KATs) using NIST SP 800-38A test vectors for CFB128.
    Reference: https://csrc.nist.gov/publications/detail/sp/800-38a/final
    """

    def setUp(self):
        """Set up NIST test vectors."""
        self.temp_dir = tempfile.mkdtemp()
        # NIST SP 800-38A AES-128 key
        self.nist_key = bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c")
        # NIST SP 800-38A CFB128 IV
        self.nist_iv = bytes.fromhex("000102030405060708090a0b0c0d0e0f")

        # NIST CFB128 test vectors (4 blocks)
        self.nist_plaintext = bytes.fromhex(
            "6bc1bee22e409f96e93d7e117393172a"
            "ae2d8a571e03ac9c9eb76fac45af8e51"
            "30c81c46a35ce411e5fbc1191a0a52ef"
            "f69f2445df4f9b17ad2b417be66c3710"
        )
        self.nist_ciphertext = bytes.fromhex(
            "3b3fd92eb72dad20333449f8e83cfb4a"
            "c8a64537a0b3a93fcde3cdad9f1ce58b"
            "26751f67a3cbb140b1808cf187a4f4df"
            "c04b05357c5d1c0eeac4c66f9ff7f2e6"
        )

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('cryptocoreedu.modes.CFBMode.generate_random_bytes')
    def test_nist_cfb_encrypt_vector(self, mock_random):
        """Test CFB encryption against NIST SP 800-38A vector."""
        mock_random.return_value = self.nist_iv

        cfb = CFBMode(self.nist_key)

        input_file = Path(self.temp_dir) / "plaintext.bin"
        encrypted_file = Path(self.temp_dir) / "encrypted.bin"

        with open(input_file, 'wb') as f:
            f.write(self.nist_plaintext)

        cfb.encrypt_file(input_file, encrypted_file)

        with open(encrypted_file, 'rb') as f:
            result = f.read()

        result_iv = result[:16]
        result_ciphertext = result[16:]

        self.assertEqual(result_iv, self.nist_iv)
        self.assertEqual(result_ciphertext, self.nist_ciphertext)

    def test_nist_cfb_decrypt_vector(self):
        """Test CFB decryption against NIST SP 800-38A vector."""
        cfb = CFBMode(self.nist_key)

        encrypted_file = Path(self.temp_dir) / "encrypted.bin"
        decrypted_file = Path(self.temp_dir) / "decrypted.bin"

        # Write IV + ciphertext
        with open(encrypted_file, 'wb') as f:
            f.write(self.nist_iv + self.nist_ciphertext)

        cfb.decrypt_file(encrypted_file, decrypted_file, iv=None)

        with open(decrypted_file, 'rb') as f:
            result = f.read()

        self.assertEqual(result, self.nist_plaintext)

    def test_nist_single_block(self):
        """Test CFB with single block from NIST vector."""
        cfb = CFBMode(self.nist_key)

        single_plaintext = bytes.fromhex("6bc1bee22e409f96e93d7e117393172a")
        single_ciphertext = bytes.fromhex("3b3fd92eb72dad20333449f8e83cfb4a")

        encrypted_file = Path(self.temp_dir) / "encrypted.bin"
        decrypted_file = Path(self.temp_dir) / "decrypted.bin"

        with open(encrypted_file, 'wb') as f:
            f.write(self.nist_iv + single_ciphertext)

        cfb.decrypt_file(encrypted_file, decrypted_file, iv=None)

        with open(decrypted_file, 'rb') as f:
            result = f.read()

        self.assertEqual(result, single_plaintext)


class TestCFBModeVariousDataSizes(unittest.TestCase):
    """Test CFB mode with various data sizes."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.key = bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c")

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


    def test_single_byte(self):
        """Test encryption of single byte."""
        cfb = CFBMode(self.key)

        input_file = Path(self.temp_dir) / "single.bin"
        encrypted_file = Path(self.temp_dir) / "encrypted.bin"
        decrypted_file = Path(self.temp_dir) / "decrypted.bin"

        with open(input_file, 'wb') as f:
            f.write(b"X")

        cfb.encrypt_file(input_file, encrypted_file)
        cfb.decrypt_file(encrypted_file, decrypted_file, iv=None)

        with open(decrypted_file, 'rb') as f:
            result = f.read()

        self.assertEqual(result, b"X")

    def test_partial_blocks(self):
        """Test encryption of various partial block sizes."""
        cfb = CFBMode(self.key)

        for size in [1, 5, 10, 15, 17, 31, 33]:
            with self.subTest(size=size):
                input_file = Path(self.temp_dir) / f"partial_{size}.bin"
                encrypted_file = Path(self.temp_dir) / f"encrypted_{size}.bin"
                decrypted_file = Path(self.temp_dir) / f"decrypted_{size}.bin"

                data = os.urandom(size)
                with open(input_file, 'wb') as f:
                    f.write(data)

                cfb.encrypt_file(input_file, encrypted_file)
                cfb.decrypt_file(encrypted_file, decrypted_file, iv=None)

                with open(decrypted_file, 'rb') as f:
                    result = f.read()

                self.assertEqual(result, data)

    def test_large_file(self):
        """Test encryption of large file."""
        cfb = CFBMode(self.key)

        input_file = Path(self.temp_dir) / "large.bin"
        encrypted_file = Path(self.temp_dir) / "encrypted.bin"
        decrypted_file = Path(self.temp_dir) / "decrypted.bin"

        data = os.urandom(10000)
        with open(input_file, 'wb') as f:
            f.write(data)

        cfb.encrypt_file(input_file, encrypted_file)
        cfb.decrypt_file(encrypted_file, decrypted_file, iv=None)

        with open(decrypted_file, 'rb') as f:
            result = f.read()

        self.assertEqual(result, data)


class TestCFBModeNegativeCases(unittest.TestCase):
    """Negative tests for CFB Mode."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.key = bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c")

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_file_not_found(self):
        """Test encryption of non-existent file."""
        cfb = CFBMode(self.key)

        with self.assertRaises(CryptoOperationError):
            cfb.encrypt_file(
                Path("/nonexistent/path/file.bin"),
                Path(self.temp_dir) / "output.bin"
            )

    def test_decrypt_file_too_short(self):
        """Test decryption of file too short for CFB."""
        cfb = CFBMode(self.key)

        short_file = Path(self.temp_dir) / "short.bin"
        output_file = Path(self.temp_dir) / "output.bin"

        with open(short_file, 'wb') as f:
            f.write(b"short")

        with self.assertRaises(CryptoOperationError) as ctx:
            cfb.decrypt_file(short_file, output_file, iv=None)

        self.assertIn("короткий", str(ctx.exception).lower())

    def test_decrypt_only_iv(self):
        """Test decryption of file containing only IV."""
        cfb = CFBMode(self.key)

        iv_only_file = Path(self.temp_dir) / "iv_only.bin"
        output_file = Path(self.temp_dir) / "output.bin"

        with open(iv_only_file, 'wb') as f:
            f.write(b"\x00" * 16)

        with self.assertRaises(CryptoOperationError) as ctx:
            cfb.decrypt_file(iv_only_file, output_file, iv=None)

        self.assertIn("данных", str(ctx.exception).lower())

    def test_decrypt_with_wrong_key(self):
        """Test decryption with wrong key produces garbage."""
        correct_key = self.key
        wrong_key = bytes.fromhex("00000000000000000000000000000000")

        cfb_encrypt = CFBMode(correct_key)
        cfb_decrypt = CFBMode(wrong_key)

        input_file = Path(self.temp_dir) / "plaintext.bin"
        encrypted_file = Path(self.temp_dir) / "encrypted.bin"
        decrypted_file = Path(self.temp_dir) / "decrypted.bin"

        original_data = b"Secret message here!"
        with open(input_file, 'wb') as f:
            f.write(original_data)

        cfb_encrypt.encrypt_file(input_file, encrypted_file)
        cfb_decrypt.decrypt_file(encrypted_file, decrypted_file, iv=None)

        with open(decrypted_file, 'rb') as f:
            result = f.read()

        # CFB with wrong key produces garbage, not error
        self.assertNotEqual(result, original_data)

    def test_bit_flip_error_propagation(self):
        """Test that bit flip in ciphertext affects decryption (CFB property)."""
        cfb = CFBMode(self.key)

        input_file = Path(self.temp_dir) / "plaintext.bin"
        encrypted_file = Path(self.temp_dir) / "encrypted.bin"
        decrypted_file = Path(self.temp_dir) / "decrypted.bin"

        original_data = b"AAAAAAAAAAAAAAAA" * 4  # 64 bytes
        with open(input_file, 'wb') as f:
            f.write(original_data)

        cfb.encrypt_file(input_file, encrypted_file)

        # Flip a bit in first ciphertext block
        with open(encrypted_file, 'rb') as f:
            data = bytearray(f.read())

        data[16] ^= 0x01  # Flip bit in first ciphertext byte (after IV)

        with open(encrypted_file, 'wb') as f:
            f.write(bytes(data))

        cfb.decrypt_file(encrypted_file, decrypted_file, iv=None)

        with open(decrypted_file, 'rb') as f:
            result = f.read()

        # In CFB, bit flip affects current block and corrupts next block
        self.assertNotEqual(result, original_data)


class TestCFBModeWithExplicitIV(unittest.TestCase):
    """Test CFB mode with explicitly provided IV."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.key = bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c")

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_decrypt_with_explicit_iv(self):
        """Test decryption with explicitly provided IV."""
        cfb = CFBMode(self.key)

        input_file = Path(self.temp_dir) / "plaintext.bin"
        encrypted_file = Path(self.temp_dir) / "encrypted.bin"
        decrypted_file = Path(self.temp_dir) / "decrypted.bin"

        original_data = b"Test data for explicit IV in CFB"
        with open(input_file, 'wb') as f:
            f.write(original_data)

        cfb.encrypt_file(input_file, encrypted_file)

        with open(encrypted_file, 'rb') as f:
            file_iv = f.read(16)
            ciphertext_only = f.read()

        with open(encrypted_file, 'wb') as f:
            f.write(ciphertext_only)

        cfb.decrypt_file(encrypted_file, decrypted_file, iv=file_iv)

        with open(decrypted_file, 'rb') as f:
            result = f.read()

        self.assertEqual(result, original_data)


if __name__ == '__main__':
    unittest.main(verbosity=2)