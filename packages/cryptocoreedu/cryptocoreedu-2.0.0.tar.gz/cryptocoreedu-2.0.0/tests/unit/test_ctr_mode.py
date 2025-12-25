"""
Unit tests for AES CTR Mode implementation.
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

from cryptocoreedu.modes.CTRMode import CTRMode
from cryptocoreedu.exceptions import CryptoOperationError


class TestCTRModeBasic(unittest.TestCase):
    """Basic functionality tests for CTRMode class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.key = bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c")

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """Test CTRMode initialization."""
        ctr = CTRMode(self.key)
        self.assertEqual(ctr.key, self.key)
        self.assertEqual(ctr.BLOCK_SIZE, 16)

    def test_encrypt_decrypt_roundtrip(self):
        """Test that encrypt followed by decrypt returns original data."""
        ctr = CTRMode(self.key)

        input_file = Path(self.temp_dir) / "plaintext.bin"
        encrypted_file = Path(self.temp_dir) / "encrypted.bin"
        decrypted_file = Path(self.temp_dir) / "decrypted.bin"

        original_data = b"Hello, World! This is a test message for CTR mode."
        with open(input_file, 'wb') as f:
            f.write(original_data)

        ctr.encrypt_file(input_file, encrypted_file)
        ctr.decrypt_file(encrypted_file, decrypted_file, iv=None)

        with open(decrypted_file, 'rb') as f:
            decrypted_data = f.read()

        self.assertEqual(decrypted_data, original_data)

    def test_stream_cipher_property(self):
        """Test that CTR produces ciphertext of same length as plaintext."""
        ctr = CTRMode(self.key)

        input_file = Path(self.temp_dir) / "plaintext.bin"
        encrypted_file = Path(self.temp_dir) / "encrypted.bin"

        original_data = b"12345"  # 5 bytes
        with open(input_file, 'wb') as f:
            f.write(original_data)

        ctr.encrypt_file(input_file, encrypted_file)

        with open(encrypted_file, 'rb') as f:
            encrypted_data = f.read()

        expected_length = 16 + len(original_data)
        self.assertEqual(len(encrypted_data), expected_length)

    def test_different_nonces_produce_different_ciphertext(self):
        """Test that different nonces produce different ciphertext."""
        ctr = CTRMode(self.key)

        input_file = Path(self.temp_dir) / "plaintext.bin"
        encrypted_file1 = Path(self.temp_dir) / "encrypted1.bin"
        encrypted_file2 = Path(self.temp_dir) / "encrypted2.bin"

        with open(input_file, 'wb') as f:
            f.write(b"Same plaintext data")

        ctr.encrypt_file(input_file, encrypted_file1)
        ctr.encrypt_file(input_file, encrypted_file2)

        with open(encrypted_file1, 'rb') as f:
            ciphertext1 = f.read()
        with open(encrypted_file2, 'rb') as f:
            ciphertext2 = f.read()

        self.assertNotEqual(ciphertext1, ciphertext2)


class TestCTRModeNISTVectors(unittest.TestCase):
    """
    Known-Answer Tests (KATs) using NIST SP 800-38A test vectors for CTR.
    Reference: https://csrc.nist.gov/publications/detail/sp/800-38a/final
    """

    def setUp(self):
        """Set up NIST test vectors."""
        self.temp_dir = tempfile.mkdtemp()
        # NIST SP 800-38A AES-128 key
        self.nist_key = bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c")
        # NIST SP 800-38A CTR initial counter
        self.nist_counter = bytes.fromhex("f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff")

        # NIST CTR test vectors (4 blocks)
        self.nist_plaintext = bytes.fromhex(
            "6bc1bee22e409f96e93d7e117393172a"
            "ae2d8a571e03ac9c9eb76fac45af8e51"
            "30c81c46a35ce411e5fbc1191a0a52ef"
            "f69f2445df4f9b17ad2b417be66c3710"
        )
        self.nist_ciphertext = bytes.fromhex(
            "874d6191b620e3261bef6864990db6ce"
            "9806f66b7970fdff8617187bb9fffdff"
            "5ae4df3edbd5d35e5b4f09020db03eab"
            "1e031dda2fbe03d1792170a0f3009cee"
        )

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('cryptocoreedu.modes.CTRMode.generate_random_bytes')
    def test_nist_ctr_encrypt_vector(self, mock_random):
        """Test CTR encryption against NIST SP 800-38A vector."""
        mock_random.return_value = self.nist_counter

        ctr = CTRMode(self.nist_key)

        input_file = Path(self.temp_dir) / "plaintext.bin"
        encrypted_file = Path(self.temp_dir) / "encrypted.bin"

        with open(input_file, 'wb') as f:
            f.write(self.nist_plaintext)

        ctr.encrypt_file(input_file, encrypted_file)

        with open(encrypted_file, 'rb') as f:
            result = f.read()

        result_iv = result[:16]
        result_ciphertext = result[16:]

        self.assertEqual(result_iv, self.nist_counter)
        self.assertEqual(result_ciphertext, self.nist_ciphertext)

    def test_nist_ctr_decrypt_vector(self):
        """Test CTR decryption against NIST SP 800-38A vector."""
        ctr = CTRMode(self.nist_key)

        encrypted_file = Path(self.temp_dir) / "encrypted.bin"
        decrypted_file = Path(self.temp_dir) / "decrypted.bin"

        with open(encrypted_file, 'wb') as f:
            f.write(self.nist_counter + self.nist_ciphertext)

        ctr.decrypt_file(encrypted_file, decrypted_file, iv=None)

        with open(decrypted_file, 'rb') as f:
            result = f.read()

        self.assertEqual(result, self.nist_plaintext)

    def test_nist_single_block(self):
        """Test CTR with single block from NIST vector."""
        ctr = CTRMode(self.nist_key)

        single_plaintext = bytes.fromhex("6bc1bee22e409f96e93d7e117393172a")
        single_ciphertext = bytes.fromhex("874d6191b620e3261bef6864990db6ce")

        encrypted_file = Path(self.temp_dir) / "encrypted.bin"
        decrypted_file = Path(self.temp_dir) / "decrypted.bin"

        with open(encrypted_file, 'wb') as f:
            f.write(self.nist_counter + single_ciphertext)

        ctr.decrypt_file(encrypted_file, decrypted_file, iv=None)

        with open(decrypted_file, 'rb') as f:
            result = f.read()

        self.assertEqual(result, single_plaintext)

    def test_ctr_symmetric_operation(self):
        """Test that CTR encryption and decryption are symmetric operations."""
        ctr = CTRMode(self.nist_key)

        # In CTR mode, encryption and decryption are the same operation
        # (XOR with keystream)
        encrypted_file = Path(self.temp_dir) / "encrypted.bin"
        decrypted_file = Path(self.temp_dir) / "decrypted.bin"

        with open(encrypted_file, 'wb') as f:
            f.write(self.nist_counter + self.nist_ciphertext)

        ctr.decrypt_file(encrypted_file, decrypted_file, iv=None)

        with open(decrypted_file, 'rb') as f:
            result = f.read()

        self.assertEqual(result, self.nist_plaintext)


class TestCTRModeVariousDataSizes(unittest.TestCase):
    """Test CTR mode with various data sizes."""

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
        ctr = CTRMode(self.key)

        input_file = Path(self.temp_dir) / "single.bin"
        encrypted_file = Path(self.temp_dir) / "encrypted.bin"
        decrypted_file = Path(self.temp_dir) / "decrypted.bin"

        with open(input_file, 'wb') as f:
            f.write(b"X")

        ctr.encrypt_file(input_file, encrypted_file)
        ctr.decrypt_file(encrypted_file, decrypted_file, iv=None)

        with open(decrypted_file, 'rb') as f:
            result = f.read()

        self.assertEqual(result, b"X")

    def test_partial_blocks(self):
        """Test encryption of various partial block sizes."""
        ctr = CTRMode(self.key)

        for size in [1, 5, 10, 15, 17, 31, 33]:
            with self.subTest(size=size):
                input_file = Path(self.temp_dir) / f"partial_{size}.bin"
                encrypted_file = Path(self.temp_dir) / f"encrypted_{size}.bin"
                decrypted_file = Path(self.temp_dir) / f"decrypted_{size}.bin"

                data = os.urandom(size)
                with open(input_file, 'wb') as f:
                    f.write(data)

                ctr.encrypt_file(input_file, encrypted_file)
                ctr.decrypt_file(encrypted_file, decrypted_file, iv=None)

                with open(decrypted_file, 'rb') as f:
                    result = f.read()

                self.assertEqual(result, data)

    def test_large_file(self):
        """Test encryption of large file."""
        ctr = CTRMode(self.key)

        input_file = Path(self.temp_dir) / "large.bin"
        encrypted_file = Path(self.temp_dir) / "encrypted.bin"
        decrypted_file = Path(self.temp_dir) / "decrypted.bin"

        data = os.urandom(10000)
        with open(input_file, 'wb') as f:
            f.write(data)

        ctr.encrypt_file(input_file, encrypted_file)
        ctr.decrypt_file(encrypted_file, decrypted_file, iv=None)

        with open(decrypted_file, 'rb') as f:
            result = f.read()

        self.assertEqual(result, data)

    def test_exactly_one_block(self):
        """Test encryption of exactly one block."""
        ctr = CTRMode(self.key)

        input_file = Path(self.temp_dir) / "oneblock.bin"
        encrypted_file = Path(self.temp_dir) / "encrypted.bin"
        decrypted_file = Path(self.temp_dir) / "decrypted.bin"

        data = b"0123456789ABCDEF"  # Exactly 16 bytes
        with open(input_file, 'wb') as f:
            f.write(data)

        ctr.encrypt_file(input_file, encrypted_file)
        ctr.decrypt_file(encrypted_file, decrypted_file, iv=None)

        with open(decrypted_file, 'rb') as f:
            result = f.read()

        self.assertEqual(result, data)


class TestCTRModeNegativeCases(unittest.TestCase):
    """Negative tests for CTR Mode."""

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
        ctr = CTRMode(self.key)

        with self.assertRaises(CryptoOperationError):
            ctr.encrypt_file(
                Path("/nonexistent/path/file.bin"),
                Path(self.temp_dir) / "output.bin"
            )

    def test_decrypt_file_too_short(self):
        """Test decryption of file too short for CTR."""
        ctr = CTRMode(self.key)

        short_file = Path(self.temp_dir) / "short.bin"
        output_file = Path(self.temp_dir) / "output.bin"

        with open(short_file, 'wb') as f:
            f.write(b"short")

        with self.assertRaises(CryptoOperationError) as ctx:
            ctr.decrypt_file(short_file, output_file, iv=None)

        self.assertIn("короткий", str(ctx.exception).lower())

    def test_decrypt_only_iv(self):
        """Test decryption of file containing only nonce/IV."""
        ctr = CTRMode(self.key)

        iv_only_file = Path(self.temp_dir) / "iv_only.bin"
        output_file = Path(self.temp_dir) / "output.bin"

        with open(iv_only_file, 'wb') as f:
            f.write(b"\x00" * 16)

        with self.assertRaises(CryptoOperationError) as ctx:
            ctr.decrypt_file(iv_only_file, output_file, iv=None)

        self.assertIn("данных", str(ctx.exception).lower())

    def test_decrypt_with_wrong_key(self):
        """Test decryption with wrong key produces garbage."""
        correct_key = self.key
        wrong_key = bytes.fromhex("00000000000000000000000000000000")

        ctr_encrypt = CTRMode(correct_key)
        ctr_decrypt = CTRMode(wrong_key)

        input_file = Path(self.temp_dir) / "plaintext.bin"
        encrypted_file = Path(self.temp_dir) / "encrypted.bin"
        decrypted_file = Path(self.temp_dir) / "decrypted.bin"

        original_data = b"Secret message here!"
        with open(input_file, 'wb') as f:
            f.write(original_data)

        ctr_encrypt.encrypt_file(input_file, encrypted_file)
        ctr_decrypt.decrypt_file(encrypted_file, decrypted_file, iv=None)

        with open(decrypted_file, 'rb') as f:
            result = f.read()

        self.assertNotEqual(result, original_data)

    def test_bit_flip_isolated_error(self):
        """Test that bit flip in CTR ciphertext only affects that position."""
        ctr = CTRMode(self.key)

        input_file = Path(self.temp_dir) / "plaintext.bin"
        encrypted_file = Path(self.temp_dir) / "encrypted.bin"
        decrypted_file = Path(self.temp_dir) / "decrypted.bin"

        original_data = b"AAAAAAAAAAAAAAAA" * 4  # 64 bytes
        with open(input_file, 'wb') as f:
            f.write(original_data)

        ctr.encrypt_file(input_file, encrypted_file)

        # Flip a bit in ciphertext
        with open(encrypted_file, 'rb') as f:
            data = bytearray(f.read())

        bit_position = 20  # Position in ciphertext (after 16-byte IV)
        data[bit_position] ^= 0x01

        with open(encrypted_file, 'wb') as f:
            f.write(bytes(data))

        ctr.decrypt_file(encrypted_file, decrypted_file, iv=None)

        with open(decrypted_file, 'rb') as f:
            result = f.read()

        # In CTR mode, bit flip only affects the corresponding plaintext byte
        self.assertNotEqual(result, original_data)
        # But other bytes should remain intact
        # Position in plaintext = bit_position - 16 (IV)
        plaintext_position = bit_position - 16
        for i, (orig, res) in enumerate(zip(original_data, result)):
            if i == plaintext_position:
                self.assertNotEqual(orig, res)
            else:
                self.assertEqual(orig, res)

    def test_nonce_reuse_vulnerability(self):
        """Test that nonce reuse is dangerous (educational test)."""
        # This test demonstrates why nonce reuse is dangerous in CTR mode
        ctr = CTRMode(self.key)

        fixed_nonce = bytes.fromhex("000102030405060708090a0b0c0d0e0f")

        plaintext1 = b"AAAAAAAAAAAAAAAA"
        plaintext2 = b"BBBBBBBBBBBBBBBB"

        encrypted_file1 = Path(self.temp_dir) / "encrypted1.bin"
        encrypted_file2 = Path(self.temp_dir) / "encrypted2.bin"

        # Manually create ciphertexts with same nonce
        from Crypto.Cipher import AES
        cipher = AES.new(self.key, AES.MODE_ECB)
        keystream = cipher.encrypt(fixed_nonce)

        ciphertext1 = bytes(a ^ b for a, b in zip(plaintext1, keystream))
        ciphertext2 = bytes(a ^ b for a, b in zip(plaintext2, keystream))

        # XOR of ciphertexts equals XOR of plaintexts (vulnerability!)
        xor_ciphertexts = bytes(a ^ b for a, b in zip(ciphertext1, ciphertext2))
        xor_plaintexts = bytes(a ^ b for a, b in zip(plaintext1, plaintext2))

        self.assertEqual(xor_ciphertexts, xor_plaintexts)


class TestCTRModeWithExplicitIV(unittest.TestCase):
    """Test CTR mode with explicitly provided IV/nonce."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.key = bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c")

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_decrypt_with_explicit_iv(self):
        """Test decryption with explicitly provided nonce."""
        ctr = CTRMode(self.key)

        input_file = Path(self.temp_dir) / "plaintext.bin"
        encrypted_file = Path(self.temp_dir) / "encrypted.bin"
        decrypted_file = Path(self.temp_dir) / "decrypted.bin"

        original_data = b"Test data for explicit nonce in CTR"
        with open(input_file, 'wb') as f:
            f.write(original_data)

        ctr.encrypt_file(input_file, encrypted_file)

        with open(encrypted_file, 'rb') as f:
            file_nonce = f.read(16)
            ciphertext_only = f.read()

        with open(encrypted_file, 'wb') as f:
            f.write(ciphertext_only)

        ctr.decrypt_file(encrypted_file, decrypted_file, iv=file_nonce)

        with open(decrypted_file, 'rb') as f:
            result = f.read()

        self.assertEqual(result, original_data)


if __name__ == '__main__':
    unittest.main(verbosity=2)