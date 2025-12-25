"""
Unit tests for HKDF (Key Derivation Function) implementation.
Tests cover basic functionality, edge cases, and negative scenarios.
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from cryptocoreedu.kdf.hkdf import hmac_sha256, derive_key, KeyHierarchy


class TestHmacSha256Function(unittest.TestCase):
    """Tests for hmac_sha256 helper function."""

    def test_basic_hmac(self):
        """Test basic HMAC-SHA256 computation."""
        key = b"key"
        message = b"message"
        result = hmac_sha256(key, message)
        self.assertIsInstance(result, bytes)
        self.assertEqual(len(result), 32)  # SHA256 output is 32 bytes

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

    def test_different_keys_different_output(self):
        """Test that different keys produce different outputs."""
        message = b"same_message"
        result1 = hmac_sha256(b"key1", message)
        result2 = hmac_sha256(b"key2", message)
        self.assertNotEqual(result1, result2)

    def test_different_messages_different_output(self):
        """Test that different messages produce different outputs."""
        key = b"same_key"
        result1 = hmac_sha256(key, b"message1")
        result2 = hmac_sha256(key, b"message2")
        self.assertNotEqual(result1, result2)


class TestDeriveKeyFunction(unittest.TestCase):
    """Tests for derive_key function."""

    def test_basic_derivation(self):
        """Test basic key derivation."""
        master_key = b"master_secret_key"
        context = "encryption"
        result = derive_key(master_key, context)
        self.assertIsInstance(result, bytes)
        self.assertEqual(len(result), 32)  # Default length

    def test_custom_length(self):
        """Test key derivation with custom length."""
        master_key = b"master_secret_key"
        context = "test"

        for length in [16, 32, 48, 64, 128]:
            with self.subTest(length=length):
                result = derive_key(master_key, context, length)
                self.assertEqual(len(result), length)

    def test_short_key_length(self):
        """Test derivation of very short keys."""
        master_key = b"master"
        context = "short"
        result = derive_key(master_key, context, 1)
        self.assertEqual(len(result), 1)

    def test_deterministic_derivation(self):
        """Test that key derivation is deterministic."""
        master_key = b"master_key"
        context = "context"
        result1 = derive_key(master_key, context, 32)
        result2 = derive_key(master_key, context, 32)
        self.assertEqual(result1, result2)

    def test_different_contexts_different_keys(self):
        """Test that different contexts produce different keys."""
        master_key = b"master_key"
        key1 = derive_key(master_key, "context1", 32)
        key2 = derive_key(master_key, "context2", 32)
        self.assertNotEqual(key1, key2)

    def test_different_master_keys_different_output(self):
        """Test that different master keys produce different derived keys."""
        context = "same_context"
        key1 = derive_key(b"master1", context, 32)
        key2 = derive_key(b"master2", context, 32)
        self.assertNotEqual(key1, key2)

    def test_empty_master_key_raises_error(self):
        """Test that empty master key raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            derive_key(b"", "context")
        self.assertIn("empty", str(ctx.exception).lower())

    def test_zero_length_raises_error(self):
        """Test that zero length raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            derive_key(b"master", "context", 0)
        self.assertIn("length", str(ctx.exception).lower())

    def test_negative_length_raises_error(self):
        """Test that negative length raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            derive_key(b"master", "context", -1)
        self.assertIn("length", str(ctx.exception).lower())

    def test_unicode_context(self):
        """Test derivation with unicode context."""
        master_key = b"master_key"
        context = "контекст"  # Russian word for "context"
        result = derive_key(master_key, context, 32)
        self.assertEqual(len(result), 32)

    def test_long_context(self):
        """Test derivation with long context."""
        master_key = b"master_key"
        context = "a" * 10000
        result = derive_key(master_key, context, 32)
        self.assertEqual(len(result), 32)

    def test_multi_block_derivation(self):
        """Test derivation requiring multiple blocks."""
        master_key = b"master_key"
        context = "multi_block"
        # Request more than 32 bytes (one HMAC-SHA256 output)
        result = derive_key(master_key, context, 100)
        self.assertEqual(len(result), 100)


class TestKeyHierarchy(unittest.TestCase):
    """Tests for KeyHierarchy class."""

    def test_init_with_bytes(self):
        """Test initialization with bytes master key."""
        master_key = b"test_master_key"
        hierarchy = KeyHierarchy(master_key)
        self.assertEqual(hierarchy.master_key, master_key)

    def test_init_with_hex_string(self):
        """Test initialization with hex string master key."""
        hex_key = "0123456789abcdef0123456789abcdef"
        hierarchy = KeyHierarchy(hex_key)
        expected = bytes.fromhex(hex_key)
        self.assertEqual(hierarchy.master_key, expected)

    def test_init_with_regular_string(self):
        """Test initialization with regular string master key."""
        string_key = "not_a_hex_string"
        hierarchy = KeyHierarchy(string_key)
        expected = string_key.encode('utf-8')
        self.assertEqual(hierarchy.master_key, expected)

    def test_init_empty_key_raises_error(self):
        """Test that empty master key raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            KeyHierarchy(b"")
        self.assertIn("empty", str(ctx.exception).lower())

    def test_derive_default_length(self):
        """Test derive with default length."""
        hierarchy = KeyHierarchy(b"master_key")
        result = hierarchy.derive("context")
        self.assertEqual(len(result), KeyHierarchy.DEFAULT_KEY_LENGTH)

    def test_derive_custom_length(self):
        """Test derive with custom length."""
        hierarchy = KeyHierarchy(b"master_key")
        result = hierarchy.derive("context", length=64)
        self.assertEqual(len(result), 64)

    def test_derive_deterministic(self):
        """Test that derive is deterministic."""
        hierarchy = KeyHierarchy(b"master_key")
        result1 = hierarchy.derive("context")
        result2 = hierarchy.derive("context")
        self.assertEqual(result1, result2)

    def test_derive_different_contexts(self):
        """Test that different contexts produce different keys."""
        hierarchy = KeyHierarchy(b"master_key")
        key1 = hierarchy.derive("encryption")
        key2 = hierarchy.derive("authentication")
        self.assertNotEqual(key1, key2)

    def test_derive_caching(self):
        """Test that caching works correctly."""
        hierarchy = KeyHierarchy(b"master_key")

        # First derivation
        result1 = hierarchy.derive("context", cache=True)
        self.assertIn(("context", 32), hierarchy._cache)

        # Second derivation should use cache
        result2 = hierarchy.derive("context", cache=True)
        self.assertEqual(result1, result2)

    def test_derive_no_cache(self):
        """Test derivation without caching."""
        hierarchy = KeyHierarchy(b"master_key")

        result = hierarchy.derive("context", cache=False)
        self.assertNotIn(("context", 32), hierarchy._cache)
        self.assertEqual(len(result), 32)

    def test_clear_cache(self):
        """Test cache clearing."""
        hierarchy = KeyHierarchy(b"master_key")

        # Populate cache
        hierarchy.derive("context1")
        hierarchy.derive("context2")
        self.assertTrue(len(hierarchy._cache) > 0)

        # Clear cache
        hierarchy.clear_cache()
        self.assertEqual(len(hierarchy._cache), 0)

    def test_derive_hex(self):
        """Test derive_hex returns hex string."""
        hierarchy = KeyHierarchy(b"master_key")
        result = hierarchy.derive_hex("context")

        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 64)  # 32 bytes = 64 hex chars
        self.assertTrue(all(c in '0123456789abcdef' for c in result))

    def test_derive_hex_custom_length(self):
        """Test derive_hex with custom length."""
        hierarchy = KeyHierarchy(b"master_key")
        result = hierarchy.derive_hex("context", length=16)

        self.assertEqual(len(result), 32)  # 16 bytes = 32 hex chars


class TestKeyHierarchyUseCases(unittest.TestCase):
    """Test real-world use cases for KeyHierarchy."""

    def test_encryption_key_derivation(self):
        """Test deriving encryption and MAC keys from master."""
        master_key = b"application_master_secret"
        hierarchy = KeyHierarchy(master_key)

        encryption_key = hierarchy.derive("encryption_key", length=32)
        mac_key = hierarchy.derive("mac_key", length=32)

        self.assertEqual(len(encryption_key), 32)
        self.assertEqual(len(mac_key), 32)
        self.assertNotEqual(encryption_key, mac_key)

    def test_session_key_derivation(self):
        """Test deriving session-specific keys."""
        master_key = b"session_master"
        hierarchy = KeyHierarchy(master_key)

        session_keys = []
        for i in range(5):
            key = hierarchy.derive(f"session_{i}", cache=False)
            session_keys.append(key)

        # All session keys should be unique
        self.assertEqual(len(set(session_keys)), 5)

    def test_hierarchical_derivation(self):
        """Test hierarchical key derivation."""
        root_hierarchy = KeyHierarchy(b"root_master")

        # Derive intermediate key
        intermediate_key = root_hierarchy.derive("intermediate")

        # Create new hierarchy from intermediate
        intermediate_hierarchy = KeyHierarchy(intermediate_key)

        # Derive final keys
        final_key1 = intermediate_hierarchy.derive("final1")
        final_key2 = intermediate_hierarchy.derive("final2")

        self.assertNotEqual(final_key1, final_key2)


class TestDeriveKeyEdgeCases(unittest.TestCase):
    """Edge case tests for key derivation."""

    def test_minimum_length(self):
        """Test minimum key length (1 byte)."""
        result = derive_key(b"master", "context", 1)
        self.assertEqual(len(result), 1)

    def test_large_key_length(self):
        """Test large key length derivation."""
        result = derive_key(b"master", "context", 1000)
        self.assertEqual(len(result), 1000)

    def test_exactly_one_block(self):
        """Test derivation of exactly one block (32 bytes)."""
        result = derive_key(b"master", "context", 32)
        self.assertEqual(len(result), 32)

    def test_exactly_two_blocks(self):
        """Test derivation of exactly two blocks (64 bytes)."""
        result = derive_key(b"master", "context", 64)
        self.assertEqual(len(result), 64)

    def test_partial_block(self):
        """Test derivation of partial block."""
        result = derive_key(b"master", "context", 50)
        self.assertEqual(len(result), 50)

    def test_empty_context(self):
        """Test derivation with empty context."""
        result = derive_key(b"master", "", 32)
        self.assertEqual(len(result), 32)

    def test_special_characters_in_context(self):
        """Test derivation with special characters in context."""
        result = derive_key(b"master", "context!@#$%^&*()", 32)
        self.assertEqual(len(result), 32)

    def test_binary_master_key(self):
        """Test derivation with binary master key."""
        master_key = bytes(range(256))
        result = derive_key(master_key, "context", 32)
        self.assertEqual(len(result), 32)


if __name__ == '__main__':
    unittest.main(verbosity=2)