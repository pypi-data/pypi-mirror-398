"""
Unit tests for HMAC-SHA256 implementation.
Tests include RFC 4231 test vectors for HMAC-SHA-256.
Reference: https://datatracker.ietf.org/doc/html/rfc4231
"""

import unittest
import tempfile
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from cryptocoreedu.mac.hmac import HMAC, hmac_data, hmac_file, verify_hmac, parse_hmac_file


class TestHMACBasic(unittest.TestCase):
    """Basic functionality tests for HMAC class."""

    def test_init_with_bytes_key(self):
        """Test HMAC initialization with bytes key."""
        key = b"secret_key"
        hmac = HMAC(key)
        self.assertIsNotNone(hmac._processed_key)
        self.assertEqual(len(hmac._processed_key), HMAC.BLOCK_SIZE)

    def test_init_with_string_key(self):
        """Test HMAC initialization with string key."""
        key = "secret_key"
        hmac = HMAC(key)
        self.assertIsNotNone(hmac._processed_key)

    def test_init_invalid_key_type(self):
        """Test that invalid key type raises TypeError."""
        with self.assertRaises(TypeError):
            HMAC(12345)

    def test_digest_returns_bytes(self):
        """Test that digest returns bytes."""
        hmac = HMAC(b"key")
        hmac.update(b"message")
        result = hmac.digest()
        self.assertIsInstance(result, bytes)
        self.assertEqual(len(result), 32)  # SHA256 output

    def test_hexdigest_returns_string(self):
        """Test that hexdigest returns hex string."""
        hmac = HMAC(b"key")
        hmac.update(b"message")
        result = hmac.hexdigest()
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 64)  # 32 bytes = 64 hex chars
        self.assertTrue(all(c in '0123456789abcdef' for c in result))

    def test_update_returns_self(self):
        """Test that update returns self for chaining."""
        hmac = HMAC(b"key")
        result = hmac.update(b"data")
        self.assertIs(result, hmac)

    def test_update_chaining(self):
        """Test update method chaining."""
        hmac = HMAC(b"key")
        hmac.update(b"hello").update(b"world")
        result = hmac.hexdigest()
        self.assertEqual(len(result), 64)

    def test_multiple_updates(self):
        """Test that multiple updates produce same result as single update."""
        hmac1 = HMAC(b"key")
        hmac1.update(b"hello")
        hmac1.update(b"world")

        hmac2 = HMAC(b"key")
        hmac2.update(b"helloworld")

        self.assertEqual(hmac1.hexdigest(), hmac2.hexdigest())

    def test_string_update(self):
        """Test update with string data."""
        hmac1 = HMAC(b"key")
        hmac1.update("message")

        hmac2 = HMAC(b"key")
        hmac2.update(b"message")

        self.assertEqual(hmac1.hexdigest(), hmac2.hexdigest())

    def test_update_invalid_type(self):
        """Test that invalid data type raises TypeError."""
        hmac = HMAC(b"key")
        with self.assertRaises(TypeError):
            hmac.update(12345)

    def test_update_after_digest_raises_error(self):
        """Test that update after digest raises RuntimeError."""
        hmac = HMAC(b"key")
        hmac.update(b"data")
        hmac.digest()

        with self.assertRaises(RuntimeError):
            hmac.update(b"more data")

    def test_digest_caching(self):
        """Test that digest result is cached."""
        hmac = HMAC(b"key")
        hmac.update(b"data")

        result1 = hmac.digest()
        result2 = hmac.digest()

        self.assertEqual(result1, result2)
        self.assertTrue(hmac._finalized)


class TestHMACRFC4231Vectors(unittest.TestCase):
    """
    Known-Answer Tests (KATs) using RFC 4231 test vectors for HMAC-SHA-256.
    Reference: https://datatracker.ietf.org/doc/html/rfc4231
    """

    def test_rfc4231_case1(self):
        """RFC 4231 Test Case 1: Short key and data."""
        # Key: 20 bytes of 0x0b
        key = bytes([0x0b] * 20)
        # Data: "Hi There"
        data = b"Hi There"
        expected = "b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7"

        hmac = HMAC(key)
        hmac.update(data)
        self.assertEqual(hmac.hexdigest(), expected)

    def test_rfc4231_case2(self):
        """RFC 4231 Test Case 2: Key = "Jefe"."""
        # Key: "Jefe"
        key = b"Jefe"
        # Data: "what do ya want for nothing?"
        data = b"what do ya want for nothing?"
        expected = "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843"

        hmac = HMAC(key)
        hmac.update(data)
        self.assertEqual(hmac.hexdigest(), expected)

    def test_rfc4231_case3(self):
        """RFC 4231 Test Case 3: Combined key and data."""
        # Key: 20 bytes of 0xaa
        key = bytes([0xaa] * 20)
        # Data: 50 bytes of 0xdd
        data = bytes([0xdd] * 50)
        expected = "773ea91e36800e46854db8ebd09181a72959098b3ef8c122d9635514ced565fe"

        hmac = HMAC(key)
        hmac.update(data)
        self.assertEqual(hmac.hexdigest(), expected)

    def test_rfc4231_case4(self):
        """RFC 4231 Test Case 4: Combined key and data with different values."""
        # Key: 25 bytes (0x01 through 0x19)
        key = bytes(range(0x01, 0x1a))
        # Data: 50 bytes of 0xcd
        data = bytes([0xcd] * 50)
        expected = "82558a389a443c0ea4cc819899f2083a85f0faa3e578f8077a2e3ff46729665b"

        hmac = HMAC(key)
        hmac.update(data)
        self.assertEqual(hmac.hexdigest(), expected)

    def test_rfc4231_case5_full(self):
        """RFC 4231 Test Case 5: Test With Truncation (full output)."""
        # Key: 20 bytes of 0x0c
        key = bytes([0x0c] * 20)
        # Data: "Test With Truncation"
        data = b"Test With Truncation"
        # Full HMAC-SHA-256 (not truncated)
        expected = "a3b6167473100ee06e0c796c2955552bfa6f7c0a6a8aef8b93f860aab0cd20c5"

        hmac = HMAC(key)
        hmac.update(data)
        self.assertEqual(hmac.hexdigest(), expected)

    def test_rfc4231_case5_truncated(self):
        """RFC 4231 Test Case 5: Test With Truncation (128 bits)."""
        # Key: 20 bytes of 0x0c
        key = bytes([0x0c] * 20)
        # Data: "Test With Truncation"
        data = b"Test With Truncation"
        # Truncated to 128 bits (16 bytes = 32 hex chars)
        expected_truncated = "a3b6167473100ee06e0c796c2955552b"

        hmac = HMAC(key)
        hmac.update(data)
        result = hmac.hexdigest()[:32]  # Truncate to 128 bits
        self.assertEqual(result, expected_truncated)

    def test_rfc4231_case6(self):
        """RFC 4231 Test Case 6: Key larger than block size."""
        # Key: 131 bytes of 0xaa (larger than 64-byte block size)
        key = bytes([0xaa] * 131)
        # Data: "Test Using Larger Than Block-Size Key - Hash Key First"
        data = b"Test Using Larger Than Block-Size Key - Hash Key First"
        expected = "60e431591ee0b67f0d8a26aacbf5b77f8e0bc6213728c5140546040f0ee37f54"

        hmac = HMAC(key)
        hmac.update(data)
        self.assertEqual(hmac.hexdigest(), expected)

    def test_rfc4231_case7(self):
        """RFC 4231 Test Case 7: Large key and large data."""
        # Key: 131 bytes of 0xaa (larger than 64-byte block size)
        key = bytes([0xaa] * 131)
        # Data: Long message
        data = (b"This is a test using a larger than block-size key and a "
                b"larger than block-size data. The key needs to be hashed "
                b"before being used by the HMAC algorithm.")
        expected = "9b09ffa71b942fcb27635fbcd5b0e944bfdc63644f0713938a7f51535c3a35e2"

        hmac = HMAC(key)
        hmac.update(data)
        self.assertEqual(hmac.hexdigest(), expected)


class TestHMACKeyProcessing(unittest.TestCase):
    """Tests for HMAC key processing."""

    def test_short_key_padding(self):
        """Test that short keys are padded to block size."""
        hmac = HMAC(b"short")
        self.assertEqual(len(hmac._processed_key), HMAC.BLOCK_SIZE)

    def test_exact_block_size_key(self):
        """Test key of exactly block size."""
        key = b"x" * HMAC.BLOCK_SIZE
        hmac = HMAC(key)
        self.assertEqual(len(hmac._processed_key), HMAC.BLOCK_SIZE)

    def test_long_key_hashing(self):
        """Test that long keys are hashed."""
        key = b"x" * (HMAC.BLOCK_SIZE + 10)
        hmac = HMAC(key)
        # After hashing, key should be padded to block size
        self.assertEqual(len(hmac._processed_key), HMAC.BLOCK_SIZE)

    def test_very_long_key(self):
        """Test very long key."""
        key = b"x" * 1000
        hmac = HMAC(key)
        self.assertEqual(len(hmac._processed_key), HMAC.BLOCK_SIZE)

    def test_empty_key(self):
        """Test empty key (should be padded)."""
        hmac = HMAC(b"")
        self.assertEqual(len(hmac._processed_key), HMAC.BLOCK_SIZE)

    def test_binary_key(self):
        """Test key with all byte values."""
        key = bytes(range(256))
        hmac = HMAC(key)
        hmac.update(b"data")
        result = hmac.hexdigest()
        self.assertEqual(len(result), 64)


class TestHMACDataFunction(unittest.TestCase):
    """Tests for hmac_data convenience function."""

    def test_basic_usage(self):
        """Test basic hmac_data usage."""
        result = hmac_data(b"key", b"message")
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 64)

    def test_matches_class(self):
        """Test that hmac_data matches HMAC class output."""
        key = b"test_key"
        data = b"test_data"

        func_result = hmac_data(key, data)

        hmac = HMAC(key)
        hmac.update(data)
        class_result = hmac.hexdigest()

        self.assertEqual(func_result, class_result)

    def test_string_key(self):
        """Test hmac_data with string key."""
        result1 = hmac_data("key", b"data")
        result2 = hmac_data(b"key", b"data")
        self.assertEqual(result1, result2)

    def test_string_data(self):
        """Test hmac_data with string data."""
        result1 = hmac_data(b"key", "data")
        result2 = hmac_data(b"key", b"data")
        self.assertEqual(result1, result2)

    def test_rfc4231_vector(self):
        """Test hmac_data against RFC 4231 vector."""
        key = b"Jefe"
        data = b"what do ya want for nothing?"
        expected = "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843"

        result = hmac_data(key, data)
        self.assertEqual(result, expected)


class TestHMACFileFunction(unittest.TestCase):
    """Tests for hmac_file function."""

    def setUp(self):
        """Set up temporary files for testing."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_file_hmac_basic(self):
        """Test HMAC of a basic file."""
        filepath = os.path.join(self.temp_dir, "test.txt")
        with open(filepath, 'wb') as f:
            f.write(b"test data")

        key = b"secret_key"
        result = hmac_file(key, filepath)
        expected = hmac_data(key, b"test data")

        self.assertEqual(result, expected)

    def test_file_hmac_empty(self):
        """Test HMAC of an empty file."""
        filepath = os.path.join(self.temp_dir, "empty.txt")
        with open(filepath, 'wb') as f:
            pass

        key = b"key"
        result = hmac_file(key, filepath)
        expected = hmac_data(key, b"")

        self.assertEqual(result, expected)

    def test_file_hmac_large(self):
        """Test HMAC of a large file (multiple chunks)."""
        filepath = os.path.join(self.temp_dir, "large.txt")
        data = b"x" * 100000
        with open(filepath, 'wb') as f:
            f.write(data)

        key = b"key"
        result = hmac_file(key, filepath)
        expected = hmac_data(key, data)

        self.assertEqual(result, expected)

    def test_file_hmac_binary(self):
        """Test HMAC of a binary file."""
        filepath = os.path.join(self.temp_dir, "binary.bin")
        data = bytes(range(256)) * 100
        with open(filepath, 'wb') as f:
            f.write(data)

        key = b"key"
        result = hmac_file(key, filepath)
        expected = hmac_data(key, data)

        self.assertEqual(result, expected)

    def test_file_hmac_string_key(self):
        """Test hmac_file with string key."""
        filepath = os.path.join(self.temp_dir, "test.txt")
        with open(filepath, 'wb') as f:
            f.write(b"data")

        result1 = hmac_file("key", filepath)
        result2 = hmac_file(b"key", filepath)

        self.assertEqual(result1, result2)

    def test_file_not_found(self):
        """Test hmac_file with non-existent file."""
        with self.assertRaises(FileNotFoundError):
            hmac_file(b"key", "/nonexistent/path/file.txt")

    def test_different_chunk_sizes(self):
        """Test that different chunk sizes produce same result."""
        filepath = os.path.join(self.temp_dir, "chunk_test.txt")
        data = b"x" * 10000
        with open(filepath, 'wb') as f:
            f.write(data)

        key = b"key"
        result1 = hmac_file(key, filepath, chunk_size=64)
        result2 = hmac_file(key, filepath, chunk_size=1024)
        result3 = hmac_file(key, filepath, chunk_size=8096)

        self.assertEqual(result1, result2)
        self.assertEqual(result2, result3)


class TestVerifyHMAC(unittest.TestCase):
    """Tests for verify_hmac function."""

    def test_matching_hmacs(self):
        """Test verification with matching HMACs."""
        hmac_value = "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843"
        self.assertTrue(verify_hmac(hmac_value, hmac_value))

    def test_non_matching_hmacs(self):
        """Test verification with non-matching HMACs."""
        hmac1 = "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843"
        hmac2 = "0000000000000000000000000000000000000000000000000000000000000000"
        self.assertFalse(verify_hmac(hmac1, hmac2))

    def test_case_insensitive(self):
        """Test that verification is case-insensitive."""
        hmac_lower = "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843"
        hmac_upper = "5BDCC146BF60754E6A042426089575C75A003F089D2739839DEC58B964EC3843"
        self.assertTrue(verify_hmac(hmac_lower, hmac_upper))

    def test_whitespace_handling(self):
        """Test that verification handles whitespace."""
        hmac1 = "  5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843  "
        hmac2 = "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843"
        self.assertTrue(verify_hmac(hmac1, hmac2))

    def test_different_lengths(self):
        """Test verification with different length HMACs."""
        hmac1 = "5bdcc146bf60754e6a042426089575c7"  # truncated
        hmac2 = "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843"
        self.assertFalse(verify_hmac(hmac1, hmac2))

    def test_single_bit_difference(self):
        """Test that single bit difference is detected."""
        hmac1 = "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843"
        hmac2 = "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3842"  # last char different
        self.assertFalse(verify_hmac(hmac1, hmac2))

    def test_timing_safe(self):
        """Test that verification uses constant-time comparison."""
        # This is a functional test - the implementation should use XOR-based comparison
        hmac1 = "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843"
        hmac2 = "0000000000000000000000000000000000000000000000000000000000000000"

        # Should still return False, but in constant time
        self.assertFalse(verify_hmac(hmac1, hmac2))


class TestParseHMACFile(unittest.TestCase):
    """Tests for parse_hmac_file function."""

    def setUp(self):
        """Set up temporary files for testing."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_parse_hmac_only(self):
        """Test parsing file with HMAC only."""
        filepath = os.path.join(self.temp_dir, "hmac.txt")
        with open(filepath, 'w') as f:
            f.write("5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843")

        hmac_value, filename = parse_hmac_file(filepath)
        self.assertEqual(hmac_value, "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843")
        self.assertIsNone(filename)

    def test_parse_hmac_with_filename(self):
        """Test parsing file with HMAC and filename."""
        filepath = os.path.join(self.temp_dir, "hmac.txt")
        with open(filepath, 'w') as f:
            f.write("5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843 data.txt")

        hmac_value, filename = parse_hmac_file(filepath)
        self.assertEqual(hmac_value, "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843")
        self.assertEqual(filename, "data.txt")

    def test_parse_uppercase_hmac(self):
        """Test parsing file with uppercase HMAC."""
        filepath = os.path.join(self.temp_dir, "hmac.txt")
        with open(filepath, 'w') as f:
            f.write("5BDCC146BF60754E6A042426089575C75A003F089D2739839DEC58B964EC3843")

        hmac_value, _ = parse_hmac_file(filepath)
        self.assertEqual(hmac_value, "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843")

    def test_parse_empty_file_raises_error(self):
        """Test that empty file raises ValueError."""
        filepath = os.path.join(self.temp_dir, "empty.txt")
        with open(filepath, 'w') as f:
            pass

        with self.assertRaises(ValueError) as ctx:
            parse_hmac_file(filepath)
        self.assertIn("пустой", str(ctx.exception).lower())

    def test_parse_invalid_hmac_raises_error(self):
        """Test that invalid HMAC raises ValueError."""
        filepath = os.path.join(self.temp_dir, "invalid.txt")
        with open(filepath, 'w') as f:
            f.write("not_a_valid_hmac_gg12")  # contains invalid chars

        with self.assertRaises(ValueError) as ctx:
            parse_hmac_file(filepath)
        self.assertIn("формат", str(ctx.exception).lower())

    def test_parse_with_whitespace(self):
        """Test parsing file with extra whitespace."""
        filepath = os.path.join(self.temp_dir, "hmac.txt")
        with open(filepath, 'w') as f:
            f.write("  5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843   file.txt  \n")

        hmac_value, filename = parse_hmac_file(filepath)
        self.assertEqual(hmac_value, "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843")
        self.assertEqual(filename, "file.txt")


class TestHMACEdgeCases(unittest.TestCase):
    """Edge case tests for HMAC."""

    def test_empty_key_and_data(self):
        """Test HMAC with empty key and data."""
        hmac = HMAC(b"")
        hmac.update(b"")
        result = hmac.hexdigest()
        self.assertEqual(len(result), 64)

    def test_single_byte_key(self):
        """Test HMAC with single byte key."""
        hmac = HMAC(b"x")
        hmac.update(b"data")
        result = hmac.hexdigest()
        self.assertEqual(len(result), 64)

    def test_single_byte_data(self):
        """Test HMAC with single byte data."""
        hmac = HMAC(b"key")
        hmac.update(b"x")
        result = hmac.hexdigest()
        self.assertEqual(len(result), 64)

    def test_key_exactly_block_size(self):
        """Test HMAC with key exactly block size."""
        key = b"x" * 64
        hmac = HMAC(key)
        hmac.update(b"data")
        result = hmac.hexdigest()
        self.assertEqual(len(result), 64)

    def test_key_one_over_block_size(self):
        """Test HMAC with key one byte over block size."""
        key = b"x" * 65
        hmac = HMAC(key)
        hmac.update(b"data")
        result = hmac.hexdigest()
        self.assertEqual(len(result), 64)

    def test_bytearray_data(self):
        """Test HMAC with bytearray data."""
        hmac = HMAC(b"key")
        hmac.update(bytearray(b"data"))
        result = hmac.hexdigest()

        hmac2 = HMAC(b"key")
        hmac2.update(b"data")
        expected = hmac2.hexdigest()

        self.assertEqual(result, expected)

    def test_memoryview_data(self):
        """Test HMAC with memoryview data."""
        data = b"test data"
        hmac = HMAC(b"key")
        hmac.update(memoryview(data))
        result = hmac.hexdigest()

        hmac2 = HMAC(b"key")
        hmac2.update(data)
        expected = hmac2.hexdigest()

        self.assertEqual(result, expected)

    def test_consistency(self):
        """Test that same inputs always produce same output."""
        key = b"consistent_key"
        data = b"consistent_data"

        results = []
        for _ in range(10):
            hmac = HMAC(key)
            hmac.update(data)
            results.append(hmac.hexdigest())

        self.assertTrue(all(r == results[0] for r in results))

    def test_unicode_key(self):
        """Test HMAC with unicode string key."""
        hmac1 = HMAC("ключ")  # Russian word for "key"
        hmac1.update(b"data")
        result = hmac1.hexdigest()

        hmac2 = HMAC("ключ".encode('utf-8'))
        hmac2.update(b"data")
        expected = hmac2.hexdigest()

        self.assertEqual(result, expected)

    def test_unicode_data(self):
        """Test HMAC with unicode string data."""
        hmac1 = HMAC(b"key")
        hmac1.update("данные")  # Russian word for "data"
        result = hmac1.hexdigest()

        hmac2 = HMAC(b"key")
        hmac2.update("данные".encode('utf-8'))
        expected = hmac2.hexdigest()

        self.assertEqual(result, expected)


class TestHMACConstants(unittest.TestCase):
    """Tests for HMAC class constants."""

    def test_block_size(self):
        """Test BLOCK_SIZE is 64 (for SHA256)."""
        self.assertEqual(HMAC.BLOCK_SIZE, 64)

    def test_output_size(self):
        """Test OUTPUT_SIZE is 32 (for SHA256)."""
        self.assertEqual(HMAC.OUTPUT_SIZE, 32)

    def test_ipad_byte(self):
        """Test IPAD_BYTE is 0x36."""
        self.assertEqual(HMAC.IPAD_BYTE, 0x36)

    def test_opad_byte(self):
        """Test OPAD_BYTE is 0x5c."""
        self.assertEqual(HMAC.OPAD_BYTE, 0x5c)


class TestHMACInternalMethods(unittest.TestCase):
    """Tests for HMAC internal methods."""

    def test_xor_bytes(self):
        """Test _xor_bytes static method."""
        a = bytes([0x00, 0xFF, 0xAA, 0x55])
        b = bytes([0xFF, 0xFF, 0x55, 0xAA])
        expected = bytes([0xFF, 0x00, 0xFF, 0xFF])

        result = HMAC._xor_bytes(a, b)
        self.assertEqual(result, expected)

    def test_xor_bytes_empty(self):
        """Test _xor_bytes with empty inputs."""
        result = HMAC._xor_bytes(b"", b"")
        self.assertEqual(result, b"")

    def test_process_key_short(self):
        """Test _process_key with short key."""
        hmac = HMAC(b"short")
        # Short key should be padded with zeros
        self.assertEqual(len(hmac._processed_key), 64)
        self.assertTrue(hmac._processed_key.endswith(b'\x00' * (64 - 5)))

    def test_process_key_long(self):
        """Test _process_key with long key."""
        long_key = b"x" * 100
        hmac = HMAC(long_key)
        # Long key should be hashed (32 bytes) then padded
        self.assertEqual(len(hmac._processed_key), 64)


if __name__ == '__main__':
    unittest.main(verbosity=2)