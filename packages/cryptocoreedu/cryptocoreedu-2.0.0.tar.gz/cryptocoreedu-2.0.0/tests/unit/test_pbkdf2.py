"""
Unit tests for PBKDF2 (Password-Based Key Derivation Function 2) implementation.
Tests include RFC 6070-style test vectors adapted for HMAC-SHA256.

Note: RFC 6070 specifies test vectors for PBKDF2-HMAC-SHA1.
For PBKDF2-HMAC-SHA256, we use vectors from RFC 7914 and other verified sources.
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from cryptocoreedu.kdf.pbkdf2 import hmac_sha256, pbkdf2_hmac_sha256, _pbkdf2_f, PBKDF2


class TestHmacSha256Function(unittest.TestCase):
    """Tests for hmac_sha256 helper function in pbkdf2 module."""

    def test_basic_hmac(self):
        """Test basic HMAC-SHA256 computation."""
        key = b"key"
        message = b"message"
        result = hmac_sha256(key, message)
        self.assertIsInstance(result, bytes)
        self.assertEqual(len(result), 32)

    def test_empty_message(self):
        """Test HMAC-SHA256 with empty message."""
        key = b"key"
        message = b""
        result = hmac_sha256(key, message)
        self.assertEqual(len(result), 32)

    def test_deterministic(self):
        """Test that HMAC-SHA256 is deterministic."""
        key = b"test_key"
        message = b"test_message"
        result1 = hmac_sha256(key, message)
        result2 = hmac_sha256(key, message)
        self.assertEqual(result1, result2)


class TestPBKDF2RFC7914Vectors(unittest.TestCase):
    """
    Known-Answer Tests (KATs) using RFC 7914 test vectors for PBKDF2-HMAC-SHA256.
    Reference: https://datatracker.ietf.org/doc/html/rfc7914#section-11
    """

    def test_rfc7914_vector_1(self):
        """RFC 7914 test vector: passwd/salt, c=1, dkLen=64."""
        password = b"passwd"
        salt = b"salt"
        iterations = 1
        dklen = 64

        expected = bytes.fromhex(
            "55ac046e56e3089fec1691c22544b605"
            "f94185216dde0465e68b9d57c20dacbc"
            "49ca9cccf179b645991664b39d77ef31"
            "7c71b845b1e30bd509112041d3a19783"
        )

        result = pbkdf2_hmac_sha256(password, salt, iterations, dklen)
        self.assertEqual(result, expected)

    def test_rfc7914_vector_2(self):
        """RFC 7914 test vector: Password/NaCl, c=80000, dkLen=64."""
        password = b"Password"
        salt = b"NaCl"
        iterations = 80000
        dklen = 64

        expected = bytes.fromhex(
            "4ddcd8f60b98be21830cee5ef22701f9"
            "641a4418d04c0414aeff08876b34ab56"
            "a1d425a1225833549adb841b51c9b317"
            "6a272bdebba1d078478f62b397f33c8d"
        )

        result = pbkdf2_hmac_sha256(password, salt, iterations, dklen)
        self.assertEqual(result, expected)


class TestPBKDF2AdditionalVectors(unittest.TestCase):
    """
    Additional verified test vectors for PBKDF2-HMAC-SHA256.
    These vectors are widely used and verified against multiple implementations.
    """

    def test_password_salt_1_iteration(self):
        """Test vector: password/salt, 1 iteration, 32 bytes."""
        password = b"password"
        salt = b"salt"
        iterations = 1
        dklen = 32

        expected = bytes.fromhex(
            "120fb6cffcf8b32c43e7225256c4f837"
            "a86548c92ccc35480805987cb70be17b"
        )

        result = pbkdf2_hmac_sha256(password, salt, iterations, dklen)
        self.assertEqual(result, expected)

    def test_password_salt_2_iterations(self):
        """Test vector: password/salt, 2 iterations, 32 bytes."""
        password = b"password"
        salt = b"salt"
        iterations = 2
        dklen = 32

        expected = bytes.fromhex(
            "ae4d0c95af6b46d32d0adff928f06dd0"
            "2a303f8ef3c251dfd6e2d85a95474c43"
        )

        result = pbkdf2_hmac_sha256(password, salt, iterations, dklen)
        self.assertEqual(result, expected)

    def test_password_salt_4096_iterations(self):
        """Test vector: password/salt, 4096 iterations, 32 bytes."""
        password = b"password"
        salt = b"salt"
        iterations = 4096
        dklen = 32

        expected = bytes.fromhex(
            "c5e478d59288c841aa530db6845c4c8d"
            "962893a001ce4e11a4963873aa98134a"
        )

        result = pbkdf2_hmac_sha256(password, salt, iterations, dklen)
        self.assertEqual(result, expected)

    def test_long_password_and_salt(self):
        """Test vector: long password and salt, 4096 iterations, 40 bytes."""
        password = b"passwordPASSWORDpassword"
        salt = b"saltSALTsaltSALTsaltSALTsaltSALTsalt"
        iterations = 4096
        dklen = 40

        expected = bytes.fromhex(
            "348c89dbcbd32b2f32d814b8116e84cf"
            "2b17347ebc1800181c4e2a1fb8dd53e1"
            "c635518c7dac47e9"
        )

        result = pbkdf2_hmac_sha256(password, salt, iterations, dklen)
        self.assertEqual(result, expected)

    def test_password_with_null_byte(self):
        """Test vector: password with null byte."""
        password = b"pass\x00word"
        salt = b"sa\x00lt"
        iterations = 4096
        dklen = 16

        # Just verify it runs and produces correct length
        result = pbkdf2_hmac_sha256(password, salt, iterations, dklen)
        self.assertEqual(len(result), 16)


class TestPBKDF2Function(unittest.TestCase):
    """Tests for pbkdf2_hmac_sha256 function."""

    def test_string_password(self):
        """Test with string password (should be encoded as UTF-8)."""
        result = pbkdf2_hmac_sha256("password", b"salt", 1, 32)
        expected = pbkdf2_hmac_sha256(b"password", b"salt", 1, 32)
        self.assertEqual(result, expected)

    def test_string_salt_utf8(self):
        """Test with non-hex string salt (should be encoded as UTF-8)."""
        result = pbkdf2_hmac_sha256(b"password", "salt", 1, 32)
        expected = pbkdf2_hmac_sha256(b"password", b"salt", 1, 32)
        self.assertEqual(result, expected)

    def test_string_salt_hex(self):
        """Test with hex string salt."""
        hex_salt = "0123456789abcdef"
        result = pbkdf2_hmac_sha256(b"password", hex_salt, 1, 32)
        expected = pbkdf2_hmac_sha256(b"password", bytes.fromhex(hex_salt), 1, 32)
        self.assertEqual(result, expected)

    def test_minimum_iterations(self):
        """Test with minimum iterations (1)."""
        result = pbkdf2_hmac_sha256(b"password", b"salt", 1, 32)
        self.assertEqual(len(result), 32)

    def test_minimum_dklen(self):
        """Test with minimum derived key length (1)."""
        result = pbkdf2_hmac_sha256(b"password", b"salt", 1, 1)
        self.assertEqual(len(result), 1)

    def test_various_dklens(self):
        """Test various derived key lengths."""
        for dklen in [1, 16, 32, 48, 64, 100, 256]:
            with self.subTest(dklen=dklen):
                result = pbkdf2_hmac_sha256(b"password", b"salt", 1, dklen)
                self.assertEqual(len(result), dklen)

    def test_deterministic(self):
        """Test that PBKDF2 is deterministic."""
        result1 = pbkdf2_hmac_sha256(b"password", b"salt", 100, 32)
        result2 = pbkdf2_hmac_sha256(b"password", b"salt", 100, 32)
        self.assertEqual(result1, result2)

    def test_different_passwords_different_output(self):
        """Test that different passwords produce different keys."""
        result1 = pbkdf2_hmac_sha256(b"password1", b"salt", 100, 32)
        result2 = pbkdf2_hmac_sha256(b"password2", b"salt", 100, 32)
        self.assertNotEqual(result1, result2)

    def test_different_salts_different_output(self):
        """Test that different salts produce different keys."""
        result1 = pbkdf2_hmac_sha256(b"password", b"salt1", 100, 32)
        result2 = pbkdf2_hmac_sha256(b"password", b"salt2", 100, 32)
        self.assertNotEqual(result1, result2)

    def test_different_iterations_different_output(self):
        """Test that different iteration counts produce different keys."""
        result1 = pbkdf2_hmac_sha256(b"password", b"salt", 1, 32)
        result2 = pbkdf2_hmac_sha256(b"password", b"salt", 2, 32)
        self.assertNotEqual(result1, result2)


class TestPBKDF2NegativeCases(unittest.TestCase):
    """Negative tests for PBKDF2."""

    def test_zero_iterations_raises_error(self):
        """Test that zero iterations raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            pbkdf2_hmac_sha256(b"password", b"salt", 0, 32)
        self.assertIn("iteration", str(ctx.exception).lower())

    def test_negative_iterations_raises_error(self):
        """Test that negative iterations raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            pbkdf2_hmac_sha256(b"password", b"salt", -1, 32)
        self.assertIn("iteration", str(ctx.exception).lower())

    def test_zero_dklen_raises_error(self):
        """Test that zero dklen raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            pbkdf2_hmac_sha256(b"password", b"salt", 1, 0)
        self.assertIn("length", str(ctx.exception).lower())

    def test_negative_dklen_raises_error(self):
        """Test that negative dklen raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            pbkdf2_hmac_sha256(b"password", b"salt", 1, -1)
        self.assertIn("length", str(ctx.exception).lower())


class TestPBKDF2InternalFunction(unittest.TestCase):
    """Tests for internal _pbkdf2_f function."""

    def test_f_function_basic(self):
        """Test basic _pbkdf2_f function."""
        result = _pbkdf2_f(b"password", b"salt", 1, 1)
        self.assertIsInstance(result, bytes)
        self.assertEqual(len(result), 32)  # One HMAC-SHA256 block

    def test_f_function_multiple_iterations(self):
        """Test _pbkdf2_f with multiple iterations."""
        result1 = _pbkdf2_f(b"password", b"salt", 1, 1)
        result2 = _pbkdf2_f(b"password", b"salt", 2, 1)
        self.assertNotEqual(result1, result2)

    def test_f_function_different_blocks(self):
        """Test _pbkdf2_f produces different output for different block numbers."""
        result1 = _pbkdf2_f(b"password", b"salt", 100, 1)
        result2 = _pbkdf2_f(b"password", b"salt", 100, 2)
        self.assertNotEqual(result1, result2)


class TestPBKDF2Class(unittest.TestCase):
    """Tests for PBKDF2 class."""

    def test_init_with_bytes_password(self):
        """Test initialization with bytes password."""
        pbkdf = PBKDF2(b"password", b"salt", 1000)
        self.assertEqual(pbkdf.password, b"password")
        self.assertEqual(pbkdf.salt, b"salt")
        self.assertEqual(pbkdf.iterations, 1000)

    def test_init_with_string_password(self):
        """Test initialization with string password."""
        pbkdf = PBKDF2("password", b"salt", 1000)
        self.assertEqual(pbkdf.password, b"password")

    def test_init_default_iterations(self):
        """Test initialization with default iterations."""
        pbkdf = PBKDF2(b"password", b"salt")
        self.assertEqual(pbkdf.iterations, PBKDF2.DEFAULT_ITERATIONS)

    def test_derive_default_length(self):
        """Test derive with default length."""
        pbkdf = PBKDF2(b"password", b"salt", 1)
        result = pbkdf.derive()
        self.assertEqual(len(result), PBKDF2.DEFAULT_KEY_LENGTH)

    def test_derive_custom_length(self):
        """Test derive with custom length."""
        pbkdf = PBKDF2(b"password", b"salt", 1)
        result = pbkdf.derive(length=64)
        self.assertEqual(len(result), 64)

    def test_derive_matches_function(self):
        """Test that class derive matches function output."""
        password = b"test_password"
        salt = b"test_salt"
        iterations = 100
        length = 32

        pbkdf = PBKDF2(password, salt, iterations)
        class_result = pbkdf.derive(length)

        func_result = pbkdf2_hmac_sha256(password, salt, iterations, length)

        self.assertEqual(class_result, func_result)

    def test_derive_hex(self):
        """Test derive_hex returns hex string."""
        pbkdf = PBKDF2(b"password", b"salt", 1)
        result = pbkdf.derive_hex(length=16)

        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 32)  # 16 bytes = 32 hex chars
        self.assertTrue(all(c in '0123456789abcdef' for c in result))

    def test_derive_hex_matches_derive(self):
        """Test that derive_hex matches derive().hex()."""
        pbkdf = PBKDF2(b"password", b"salt", 100)

        hex_result = pbkdf.derive_hex(length=32)
        bytes_result = pbkdf.derive(length=32)

        self.assertEqual(hex_result, bytes_result.hex())


class TestPBKDF2ClassConstants(unittest.TestCase):
    """Tests for PBKDF2 class constants."""

    def test_default_iterations_value(self):
        """Test default iterations is reasonable for security."""
        self.assertGreaterEqual(PBKDF2.DEFAULT_ITERATIONS, 10000)

    def test_default_key_length_value(self):
        """Test default key length is 32 bytes (256 bits)."""
        self.assertEqual(PBKDF2.DEFAULT_KEY_LENGTH, 32)

    def test_hash_output_size_value(self):
        """Test hash output size is correct for SHA256."""
        self.assertEqual(PBKDF2.HASH_OUTPUT_SIZE, 32)


class TestPBKDF2EdgeCases(unittest.TestCase):
    """Edge case tests for PBKDF2."""

    def test_empty_password(self):
        """Test with empty password."""
        result = pbkdf2_hmac_sha256(b"", b"salt", 1, 32)
        self.assertEqual(len(result), 32)

    def test_empty_salt(self):
        """Test with empty salt."""
        result = pbkdf2_hmac_sha256(b"password", b"", 1, 32)
        self.assertEqual(len(result), 32)

    def test_unicode_password(self):
        """Test with unicode password."""
        result = pbkdf2_hmac_sha256("пароль", b"salt", 1, 32)  # Russian "password"
        self.assertEqual(len(result), 32)

    def test_binary_password(self):
        """Test with binary password containing all byte values."""
        password = bytes(range(256))
        result = pbkdf2_hmac_sha256(password, b"salt", 1, 32)
        self.assertEqual(len(result), 32)

    def test_binary_salt(self):
        """Test with binary salt containing all byte values."""
        salt = bytes(range(256))
        result = pbkdf2_hmac_sha256(b"password", salt, 1, 32)
        self.assertEqual(len(result), 32)

    def test_multi_block_output(self):
        """Test output requiring multiple HMAC blocks."""
        # Request more than 32 bytes
        result = pbkdf2_hmac_sha256(b"password", b"salt", 1, 100)
        self.assertEqual(len(result), 100)

    def test_exactly_one_block(self):
        """Test output of exactly one block (32 bytes)."""
        result = pbkdf2_hmac_sha256(b"password", b"salt", 1, 32)
        self.assertEqual(len(result), 32)

    def test_exactly_two_blocks(self):
        """Test output of exactly two blocks (64 bytes)."""
        result = pbkdf2_hmac_sha256(b"password", b"salt", 1, 64)
        self.assertEqual(len(result), 64)

    def test_partial_second_block(self):
        """Test output requiring partial second block."""
        result = pbkdf2_hmac_sha256(b"password", b"salt", 1, 50)
        self.assertEqual(len(result), 50)

    def test_very_long_output(self):
        """Test very long derived key."""
        result = pbkdf2_hmac_sha256(b"password", b"salt", 1, 1000)
        self.assertEqual(len(result), 1000)


class TestPBKDF2Consistency(unittest.TestCase):
    """Consistency tests for PBKDF2."""

    def test_prefix_consistency(self):
        """Test that shorter outputs are prefixes of longer outputs."""
        full = pbkdf2_hmac_sha256(b"password", b"salt", 100, 64)
        partial = pbkdf2_hmac_sha256(b"password", b"salt", 100, 32)
        self.assertEqual(full[:32], partial)

    def test_repeated_derivation(self):
        """Test that repeated derivations produce same result."""
        results = []
        for _ in range(5):
            result = pbkdf2_hmac_sha256(b"password", b"salt", 100, 32)
            results.append(result)

        self.assertTrue(all(r == results[0] for r in results))


if __name__ == '__main__':
    unittest.main(verbosity=2)