"""
Unit tests for SHA256 implementation.
Tests based on NIST FIPS 180-4 test vectors and additional edge cases.
"""

import unittest
import tempfile
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cryptocoreedu.hash.sha256 import SHA256, sha256_data, sha256_file


class TestSHA256Basic(unittest.TestCase):
    """Basic functionality tests for SHA256 class."""

    def test_init(self):
        """Test SHA256 initialization."""
        sha = SHA256()
        self.assertIsNotNone(sha.h)
        self.assertEqual(len(sha.h), 8)
        self.assertEqual(len(sha.buffer), 0)
        self.assertEqual(sha.total_length, 0)
        self.assertFalse(sha.finalized)

    def test_reset(self):
        """Test SHA256 reset functionality."""
        sha = SHA256()
        sha.update(b"test data")
        sha.reset()
        self.assertEqual(len(sha.buffer), 0)
        self.assertEqual(sha.total_length, 0)
        self.assertFalse(sha.finalized)

    def test_hexdigest_returns_string(self):
        """Test that hexdigest returns a string."""
        sha = SHA256()
        sha.update(b"test")
        result = sha.hexdigest()
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 64)  # SHA256 produces 64 hex chars

    def test_digest_returns_bytes(self):
        """Test that digest returns bytes."""
        sha = SHA256()
        sha.update(b"test")
        result = sha.digest()
        self.assertIsInstance(result, bytes)
        self.assertEqual(len(result), 32)  # SHA256 produces 32 bytes

    def test_multiple_updates(self):
        """Test that multiple updates produce same result as single update."""
        sha1 = SHA256()
        sha1.update(b"hello")
        sha1.update(b"world")

        sha2 = SHA256()
        sha2.update(b"helloworld")

        self.assertEqual(sha1.hexdigest(), sha2.hexdigest())

    def test_empty_update(self):
        """Test update with empty data."""
        sha = SHA256()
        sha.update(b"")
        sha.update(b"test")
        sha.update(b"")

        sha2 = SHA256()
        sha2.update(b"test")

        self.assertEqual(sha.hexdigest(), sha2.hexdigest())


class TestSHA256NISTVectors(unittest.TestCase):
    """
    Known-Answer Tests (KATs) using NIST FIPS 180-4 test vectors.
    Reference: https://csrc.nist.gov/CSRC/media/Projects/Cryptographic-Standards-and-Guidelines/documents/examples/SHA256.pdf
    """

    def test_empty_string(self):
        """Test SHA256 of empty string (NIST test vector)."""
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        sha = SHA256()
        result = sha.hexdigest()
        self.assertEqual(result, expected)

    def test_abc(self):
        """Test SHA256 of 'abc' (NIST FIPS 180-4 example)."""
        expected = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        sha = SHA256()
        sha.update(b"abc")
        result = sha.hexdigest()
        self.assertEqual(result, expected)

    def test_two_block_message(self):
        """Test SHA256 of two-block message (NIST FIPS 180-4 example)."""
        # "abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq"
        message = b"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq"
        expected = "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1"
        sha = SHA256()
        sha.update(message)
        result = sha.hexdigest()
        self.assertEqual(result, expected)

    def test_long_message(self):
        """Test SHA256 of longer message (NIST example)."""
        # "abcdefghbcdefghicdefghijdefghijkefghijklfghijklmghijklmnhijklmnoijklmnopjklmnopqklmnopqrlmnopqrsmnopqrstnopqrstu"
        message = b"abcdefghbcdefghicdefghijdefghijkefghijklfghijklmghijklmnhijklmnoijklmnopjklmnopqklmnopqrlmnopqrsmnopqrstnopqrstu"
        expected = "cf5b16a778af8380036ce59e7b0492370b249b11e8f07a51afac45037afee9d1"
        sha = SHA256()
        sha.update(message)
        result = sha.hexdigest()
        self.assertEqual(result, expected)

    def test_one_million_a(self):
        """Test SHA256 of one million 'a' characters (NIST test vector)."""
        # Correct NIST FIPS 180-4 test vector for 1,000,000 'a' characters
        expected = "cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0"
        sha = SHA256()
        # Update in chunks to avoid memory issues
        chunk = b"a" * 10000
        for _ in range(100):
            sha.update(chunk)
        result = sha.hexdigest()
        self.assertEqual(result, expected)

    def test_448_bits(self):
        """Test SHA256 with exactly 448 bits (56 bytes) - edge case for padding."""
        # 56 bytes message
        message = b"a" * 56
        sha = SHA256()
        sha.update(message)
        result = sha.hexdigest()
        # Verify output is valid (64 hex chars)
        self.assertEqual(len(result), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in result))

    def test_512_bits(self):
        """Test SHA256 with exactly 512 bits (64 bytes) - one full block."""
        message = b"a" * 64
        sha = SHA256()
        sha.update(message)
        result = sha.hexdigest()
        self.assertEqual(len(result), 64)

    def test_nist_short_msg_vectors(self):
        """Additional NIST short message test vectors."""
        test_vectors = [
            # (message_hex, expected_hash)
            ("", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
            ("616263", "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"),  # "abc"
            (
            "6162636462636465636465666465666765666768666768696768696a68696a6b696a6b6c6a6b6c6d6b6c6d6e6c6d6e6f6d6e6f706e6f7071",
            "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1"),
        ]

        for msg_hex, expected in test_vectors:
            with self.subTest(msg_hex=msg_hex):
                message = bytes.fromhex(msg_hex)
                sha = SHA256()
                sha.update(message)
                self.assertEqual(sha.hexdigest(), expected)


class TestSHA256DataFunction(unittest.TestCase):
    """Tests for sha256_data convenience function."""

    def test_bytes_input(self):
        """Test sha256_data with bytes input."""
        result = sha256_data(b"abc")
        expected = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        self.assertEqual(result, expected)

    def test_string_input(self):
        """Test sha256_data with string input."""
        result = sha256_data("abc")
        expected = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        self.assertEqual(result, expected)

    def test_empty_input(self):
        """Test sha256_data with empty input."""
        result = sha256_data(b"")
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        self.assertEqual(result, expected)

    def test_unicode_string(self):
        """Test sha256_data with unicode string."""
        result = sha256_data("тест")
        # Should encode as UTF-8 and hash
        sha = SHA256()
        sha.update("тест".encode('utf-8'))
        expected = sha.hexdigest()
        self.assertEqual(result, expected)


class TestSHA256FileFunction(unittest.TestCase):
    """Tests for sha256_file function."""

    def setUp(self):
        """Set up temporary files for testing."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_file_hash_basic(self):
        """Test hashing a basic file."""
        filepath = os.path.join(self.temp_dir, "test.txt")
        with open(filepath, 'wb') as f:
            f.write(b"abc")

        result = sha256_file(filepath)
        expected = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        self.assertEqual(result, expected)

    def test_file_hash_empty(self):
        """Test hashing an empty file."""
        filepath = os.path.join(self.temp_dir, "empty.txt")
        with open(filepath, 'wb') as f:
            pass

        result = sha256_file(filepath)
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        self.assertEqual(result, expected)

    def test_file_hash_large(self):
        """Test hashing a larger file (multiple chunks)."""
        filepath = os.path.join(self.temp_dir, "large.txt")
        data = b"a" * 100000
        with open(filepath, 'wb') as f:
            f.write(data)

        result = sha256_file(filepath)
        expected = sha256_data(data)
        self.assertEqual(result, expected)

    def test_file_hash_binary(self):
        """Test hashing a file with binary content."""
        filepath = os.path.join(self.temp_dir, "binary.bin")
        data = bytes(range(256))
        with open(filepath, 'wb') as f:
            f.write(data)

        result = sha256_file(filepath)
        expected = sha256_data(data)
        self.assertEqual(result, expected)

    def test_file_different_chunk_sizes(self):
        """Test that different chunk sizes produce same result."""
        filepath = os.path.join(self.temp_dir, "chunk_test.txt")
        data = b"x" * 10000
        with open(filepath, 'wb') as f:
            f.write(data)

        result1 = sha256_file(filepath, chunk_size=64)
        result2 = sha256_file(filepath, chunk_size=1024)
        result3 = sha256_file(filepath, chunk_size=8192)

        self.assertEqual(result1, result2)
        self.assertEqual(result2, result3)


class TestSHA256NegativeCases(unittest.TestCase):
    """Negative tests for SHA256."""

    def test_update_after_finalize(self):
        """Test that update after digest raises error."""
        sha = SHA256()
        sha.update(b"test")
        sha.digest()  # This should finalize

        with self.assertRaises(RuntimeError):
            sha.update(b"more data")

    def test_file_not_found(self):
        """Test that hashing non-existent file raises error."""
        with self.assertRaises(FileNotFoundError):
            sha256_file("/nonexistent/path/to/file.txt")

    def test_file_permission_error(self):
        """Test handling of permission errors (platform dependent)."""
        # This test might be skipped on some platforms
        if os.name == 'nt':  # Windows
            self.skipTest("Permission test not reliable on Windows")

        temp_dir = tempfile.mkdtemp()
        try:
            filepath = os.path.join(temp_dir, "noperm.txt")
            with open(filepath, 'wb') as f:
                f.write(b"test")
            os.chmod(filepath, 0o000)

            with self.assertRaises(PermissionError):
                sha256_file(filepath)
        finally:
            os.chmod(filepath, 0o644)
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestSHA256EdgeCases(unittest.TestCase):
    """Edge case tests for SHA256."""

    def test_exactly_one_block(self):
        """Test message that is exactly one block (64 bytes)."""
        message = b"0123456789abcdef" * 4  # 64 bytes
        sha = SHA256()
        sha.update(message)
        result = sha.hexdigest()
        self.assertEqual(len(result), 64)

    def test_block_boundary(self):
        """Test messages at block boundaries."""
        for size in [63, 64, 65, 127, 128, 129]:
            with self.subTest(size=size):
                message = b"x" * size
                sha = SHA256()
                sha.update(message)
                result = sha.hexdigest()
                self.assertEqual(len(result), 64)

    def test_single_byte_updates(self):
        """Test updating one byte at a time."""
        message = b"abcdefghij"

        sha1 = SHA256()
        for byte in message:
            sha1.update(bytes([byte]))

        sha2 = SHA256()
        sha2.update(message)

        self.assertEqual(sha1.hexdigest(), sha2.hexdigest())

    def test_all_zero_bytes(self):
        """Test hashing all zero bytes."""
        message = b"\x00" * 100
        sha = SHA256()
        sha.update(message)
        result = sha.hexdigest()
        self.assertEqual(len(result), 64)

    def test_all_ff_bytes(self):
        """Test hashing all 0xFF bytes."""
        message = b"\xff" * 100
        sha = SHA256()
        sha.update(message)
        result = sha.hexdigest()
        self.assertEqual(len(result), 64)

    def test_consistency(self):
        """Test that same input always produces same output."""
        message = b"consistency test"
        results = []
        for _ in range(10):
            sha = SHA256()
            sha.update(message)
            results.append(sha.hexdigest())

        self.assertTrue(all(r == results[0] for r in results))


class TestSHA256InternalFunctions(unittest.TestCase):
    """Tests for internal SHA256 functions (via class wrappers)."""

    def test_rotr(self):
        """Test right rotation function."""
        sha = SHA256()
        # Test known rotation
        import numpy as np
        x = np.uint32(0x80000000)
        result = sha._rotr(1, x)
        self.assertEqual(result, 0x40000000)

    def test_shr(self):
        """Test right shift function."""
        sha = SHA256()
        import numpy as np
        x = np.uint32(0x80000000)
        result = sha._shr(1, x)
        self.assertEqual(result, 0x40000000)

    def test_ch_function(self):
        """Test choice function."""
        sha = SHA256()
        import numpy as np
        x = np.uint32(0xFFFFFFFF)
        y = np.uint32(0x12345678)
        z = np.uint32(0x87654321)
        result = sha._ch(x, y, z)
        self.assertEqual(result, y)  # When x is all 1s, result is y

    def test_maj_function(self):
        """Test majority function."""
        sha = SHA256()
        import numpy as np
        x = np.uint32(0xFF00FF00)
        y = np.uint32(0xFF00FF00)
        z = np.uint32(0x00FF00FF)
        result = sha._maj(x, y, z)
        self.assertEqual(result, 0xFF00FF00)  # Majority wins


if __name__ == '__main__':
    unittest.main(verbosity=2)