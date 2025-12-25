"""
Unit tests for SHA3-256 implementation.
Tests based on NIST FIPS 202 test vectors and additional edge cases.
"""

import unittest
import tempfile
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cryptocoreedu.hash.sha3_256 import SHA3_256, sha3_256_data, sha3_256_file


class TestSHA3_256Basic(unittest.TestCase):
    """Basic functionality tests for SHA3_256 class."""

    def test_init(self):
        """Test SHA3_256 initialization."""
        sha = SHA3_256()
        self.assertIsNotNone(sha.state)
        self.assertEqual(sha.state.shape, (5, 5))
        self.assertEqual(len(sha.buffer), 0)
        self.assertFalse(sha.finalized)

    def test_reset(self):
        """Test SHA3_256 reset functionality."""
        sha = SHA3_256()
        sha.update(b"test data")
        sha.reset()
        self.assertEqual(len(sha.buffer), 0)
        self.assertFalse(sha.finalized)
        # State should be all zeros after reset
        self.assertTrue((sha.state == 0).all())

    def test_hexdigest_returns_string(self):
        """Test that hexdigest returns a string."""
        sha = SHA3_256()
        sha.update(b"test")
        result = sha.hexdigest()
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 64)  # SHA3-256 produces 64 hex chars

    def test_digest_returns_bytes(self):
        """Test that digest returns bytes."""
        sha = SHA3_256()
        sha.update(b"test")
        result = sha.digest()
        self.assertIsInstance(result, bytes)
        self.assertEqual(len(result), 32)  # SHA3-256 produces 32 bytes

    def test_multiple_updates(self):
        """Test that multiple updates produce same result as single update."""
        sha1 = SHA3_256()
        sha1.update(b"hello")
        sha1.update(b"world")

        sha2 = SHA3_256()
        sha2.update(b"helloworld")

        self.assertEqual(sha1.hexdigest(), sha2.hexdigest())

    def test_empty_update(self):
        """Test update with empty data."""
        sha = SHA3_256()
        sha.update(b"")
        sha.update(b"test")
        sha.update(b"")

        sha2 = SHA3_256()
        sha2.update(b"test")

        self.assertEqual(sha.hexdigest(), sha2.hexdigest())

    def test_copy(self):
        """Test copy functionality."""
        sha1 = SHA3_256()
        sha1.update(b"hello")
        sha2 = sha1.copy()

        sha1.update(b"world")
        sha2.update(b"world")

        self.assertEqual(sha1.hexdigest(), sha2.hexdigest())

    def test_copy_independence(self):
        """Test that copy is independent of original."""
        sha1 = SHA3_256()
        sha1.update(b"hello")
        sha2 = sha1.copy()

        sha1.update(b"world")
        sha2.update(b"python")

        self.assertNotEqual(sha1.hexdigest(), sha2.hexdigest())


class TestSHA3_256NISTVectors(unittest.TestCase):
    """
    Known-Answer Tests (KATs) using NIST FIPS 202 test vectors.
    Reference: https://csrc.nist.gov/Projects/Cryptographic-Algorithm-Validation-Program/Secure-Hashing
    """

    def test_empty_string(self):
        """Test SHA3-256 of empty string (NIST test vector)."""
        expected = "a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a"
        sha = SHA3_256()
        result = sha.hexdigest()
        self.assertEqual(result, expected)

    def test_abc(self):
        """Test SHA3-256 of 'abc' (NIST FIPS 202 example)."""
        expected = "3a985da74fe225b2045c172d6bd390bd855f086e3e9d525b46bfe24511431532"
        sha = SHA3_256()
        sha.update(b"abc")
        result = sha.hexdigest()
        self.assertEqual(result, expected)

    def test_empty_via_data_function(self):
        """Test SHA3-256 of empty string via convenience function."""
        expected = "a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a"
        result = sha3_256_data(b"")
        self.assertEqual(result, expected)

    def test_abc_via_data_function(self):
        """Test SHA3-256 of 'abc' via convenience function."""
        expected = "3a985da74fe225b2045c172d6bd390bd855f086e3e9d525b46bfe24511431532"
        result = sha3_256_data(b"abc")
        self.assertEqual(result, expected)

    def test_nist_short_vectors(self):
        """NIST FIPS 202 short message test vectors."""
        test_vectors = [
            # (message_hex, expected_hash)
            ("", "a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a"),
            ("616263", "3a985da74fe225b2045c172d6bd390bd855f086e3e9d525b46bfe24511431532"),  # "abc"
            ("", "a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a"),  # empty
        ]

        for msg_hex, expected in test_vectors:
            with self.subTest(msg_hex=msg_hex):
                message = bytes.fromhex(msg_hex)
                sha = SHA3_256()
                sha.update(message)
                self.assertEqual(sha.hexdigest(), expected)

    def test_long_message(self):
        """Test SHA3-256 with longer message from NIST."""
        # 200 repetitions of 0xa3 byte
        message = bytes([0xa3] * 200)
        sha = SHA3_256()
        sha.update(message)
        result = sha.hexdigest()
        # Verify output format
        self.assertEqual(len(result), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in result))

    def test_nist_long_msg_vector(self):
        """NIST long message test vector."""
        # "abcdefghbcdefghicdefghijdefghijkefghijklfghijklmghijklmnhijklmnoijklmnopjklmnopqklmnopqrlmnopqrsmnopqrstnopqrstu"
        message = b"abcdefghbcdefghicdefghijdefghijkefghijklfghijklmghijklmnhijklmnoijklmnopjklmnopqklmnopqrlmnopqrsmnopqrstnopqrstu"
        expected = "916f6061fe879741ca6469b43971dfdb28b1a32dc36cb3254e812be27aad1d18"
        sha = SHA3_256()
        sha.update(message)
        result = sha.hexdigest()
        self.assertEqual(result, expected)

    def test_one_million_a(self):
        """Test SHA3-256 of one million 'a' characters."""
        expected = "5c8875ae474a3634ba4fd55ec85bffd661f32aca75c6d699d0cdcb6c115891c1"
        sha = SHA3_256()
        # Update in chunks to avoid memory issues
        chunk = b"a" * 10000
        for _ in range(100):
            sha.update(chunk)
        result = sha.hexdigest()
        self.assertEqual(result, expected)


class TestSHA3_256DataFunction(unittest.TestCase):
    """Tests for sha3_256_data convenience function."""

    def test_bytes_input(self):
        """Test sha3_256_data with bytes input."""
        result = sha3_256_data(b"abc")
        expected = "3a985da74fe225b2045c172d6bd390bd855f086e3e9d525b46bfe24511431532"
        self.assertEqual(result, expected)

    def test_string_input(self):
        """Test sha3_256_data with string input."""
        result = sha3_256_data("abc")
        expected = "3a985da74fe225b2045c172d6bd390bd855f086e3e9d525b46bfe24511431532"
        self.assertEqual(result, expected)

    def test_empty_input(self):
        """Test sha3_256_data with empty input."""
        result = sha3_256_data(b"")
        expected = "a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a"
        self.assertEqual(result, expected)

    def test_unicode_string(self):
        """Test sha3_256_data with unicode string."""
        result = sha3_256_data("тест")
        # Should encode as UTF-8 and hash
        sha = SHA3_256()
        sha.update("тест".encode('utf-8'))
        expected = sha.hexdigest()
        self.assertEqual(result, expected)


class TestSHA3_256FileFunction(unittest.TestCase):
    """Tests for sha3_256_file function."""

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

        result = sha3_256_file(filepath)
        expected = "3a985da74fe225b2045c172d6bd390bd855f086e3e9d525b46bfe24511431532"
        self.assertEqual(result, expected)

    def test_file_hash_empty(self):
        """Test hashing an empty file."""
        filepath = os.path.join(self.temp_dir, "empty.txt")
        with open(filepath, 'wb') as f:
            pass

        result = sha3_256_file(filepath)
        expected = "a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a"
        self.assertEqual(result, expected)

    def test_file_hash_large(self):
        """Test hashing a larger file (multiple chunks)."""
        filepath = os.path.join(self.temp_dir, "large.txt")
        data = b"a" * 100000
        with open(filepath, 'wb') as f:
            f.write(data)

        result = sha3_256_file(filepath)
        expected = sha3_256_data(data)
        self.assertEqual(result, expected)

    def test_file_hash_binary(self):
        """Test hashing a file with binary content."""
        filepath = os.path.join(self.temp_dir, "binary.bin")
        data = bytes(range(256))
        with open(filepath, 'wb') as f:
            f.write(data)

        result = sha3_256_file(filepath)
        expected = sha3_256_data(data)
        self.assertEqual(result, expected)

    def test_file_different_chunk_sizes(self):
        """Test that different chunk sizes produce same result."""
        filepath = os.path.join(self.temp_dir, "chunk_test.txt")
        data = b"x" * 10000
        with open(filepath, 'wb') as f:
            f.write(data)

        result1 = sha3_256_file(filepath, chunk_size=136)
        result2 = sha3_256_file(filepath, chunk_size=1024)
        result3 = sha3_256_file(filepath, chunk_size=8192)

        self.assertEqual(result1, result2)
        self.assertEqual(result2, result3)


class TestSHA3_256NegativeCases(unittest.TestCase):
    """Negative tests for SHA3_256."""

    def test_update_after_finalize(self):
        """Test that update after digest raises error."""
        sha = SHA3_256()
        sha.update(b"test")
        sha.digest()  # This should finalize

        with self.assertRaises(RuntimeError):
            sha.update(b"more data")

    def test_file_not_found(self):
        """Test that hashing non-existent file raises error."""
        with self.assertRaises(FileNotFoundError):
            sha3_256_file("/nonexistent/path/to/file.txt")

    def test_file_permission_error(self):
        """Test handling of permission errors (platform dependent)."""
        if os.name == 'nt':  # Windows
            self.skipTest("Permission test not reliable on Windows")

        temp_dir = tempfile.mkdtemp()
        try:
            filepath = os.path.join(temp_dir, "noperm.txt")
            with open(filepath, 'wb') as f:
                f.write(b"test")
            os.chmod(filepath, 0o000)

            with self.assertRaises(PermissionError):
                sha3_256_file(filepath)
        finally:
            os.chmod(filepath, 0o644)
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestSHA3_256EdgeCases(unittest.TestCase):
    """Edge case tests for SHA3_256."""

    def test_rate_boundary(self):
        """Test messages at rate boundaries (136 bytes for SHA3-256)."""
        rate_bytes = 136
        for size in [rate_bytes - 1, rate_bytes, rate_bytes + 1,
                     rate_bytes * 2 - 1, rate_bytes * 2, rate_bytes * 2 + 1]:
            with self.subTest(size=size):
                message = b"x" * size
                sha = SHA3_256()
                sha.update(message)
                result = sha.hexdigest()
                self.assertEqual(len(result), 64)

    def test_single_byte_updates(self):
        """Test updating one byte at a time."""
        message = b"abcdefghij"

        sha1 = SHA3_256()
        for byte in message:
            sha1.update(bytes([byte]))

        sha2 = SHA3_256()
        sha2.update(message)

        self.assertEqual(sha1.hexdigest(), sha2.hexdigest())

    def test_all_zero_bytes(self):
        """Test hashing all zero bytes."""
        message = b"\x00" * 100
        sha = SHA3_256()
        sha.update(message)
        result = sha.hexdigest()
        self.assertEqual(len(result), 64)

    def test_all_ff_bytes(self):
        """Test hashing all 0xFF bytes."""
        message = b"\xff" * 100
        sha = SHA3_256()
        sha.update(message)
        result = sha.hexdigest()
        self.assertEqual(len(result), 64)

    def test_consistency(self):
        """Test that same input always produces same output."""
        message = b"consistency test"
        results = []
        for _ in range(10):
            sha = SHA3_256()
            sha.update(message)
            results.append(sha.hexdigest())

        self.assertTrue(all(r == results[0] for r in results))

    def test_padding_edge_case_1_byte(self):
        """Test padding when exactly 1 byte needed."""
        # Message length = rate - 1 = 135 bytes
        message = b"x" * 135
        sha = SHA3_256()
        sha.update(message)
        result = sha.hexdigest()
        self.assertEqual(len(result), 64)

    def test_padding_edge_case_full_block(self):
        """Test padding when full padding block needed."""
        # Message length = rate = 136 bytes
        message = b"x" * 136
        sha = SHA3_256()
        sha.update(message)
        result = sha.hexdigest()
        self.assertEqual(len(result), 64)


class TestSHA3_256StringUpdate(unittest.TestCase):
    """Test string handling in update method."""

    def test_string_update(self):
        """Test that update accepts strings and encodes as UTF-8."""
        sha = SHA3_256()
        sha.update("hello")
        result1 = sha.hexdigest()

        sha2 = SHA3_256()
        sha2.update(b"hello")
        result2 = sha2.hexdigest()

        self.assertEqual(result1, result2)

    def test_unicode_update(self):
        """Test update with unicode string."""
        sha = SHA3_256()
        sha.update("日本語")
        result = sha.hexdigest()

        sha2 = SHA3_256()
        sha2.update("日本語".encode('utf-8'))
        expected = sha2.hexdigest()

        self.assertEqual(result, expected)


class TestSHA3_256Constants(unittest.TestCase):
    """Test SHA3-256 constants and parameters."""

    def test_rate_bits(self):
        """Test that rate is correct for SHA3-256."""
        sha = SHA3_256()
        self.assertEqual(sha.RATE_BITS, 1088)

    def test_rate_bytes(self):
        """Test that rate in bytes is correct for SHA3-256."""
        sha = SHA3_256()
        self.assertEqual(sha.RATE_BYTES, 136)

    def test_capacity_bits(self):
        """Test that capacity is correct for SHA3-256."""
        sha = SHA3_256()
        self.assertEqual(sha.CAPACITY_BITS, 512)

    def test_output_bytes(self):
        """Test that output length is correct for SHA3-256."""
        sha = SHA3_256()
        self.assertEqual(sha.OUTPUT_BYTES, 32)

    def test_domain_suffix(self):
        """Test that domain suffix is correct for SHA3."""
        sha = SHA3_256()
        self.assertEqual(sha.DOMAIN_SUFFIX, 0x06)


class TestSHA3_256CopyAfterDigest(unittest.TestCase):
    """Test copy behavior after digest has been called."""

    def test_copy_after_digest(self):
        """Test copying object after digest has been computed."""
        sha1 = SHA3_256()
        sha1.update(b"test")
        digest1 = sha1.digest()

        sha2 = sha1.copy()
        digest2 = sha2.digest()

        self.assertEqual(digest1, digest2)

    def test_copy_preserves_finalized_state(self):
        """Test that copy preserves finalized flag."""
        sha1 = SHA3_256()
        sha1.update(b"test")
        sha1.digest()
        self.assertTrue(sha1.finalized)

        sha2 = sha1.copy()
        self.assertTrue(sha2.finalized)


if __name__ == '__main__':
    unittest.main(verbosity=2)