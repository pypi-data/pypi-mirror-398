"""Tests for the crypto_utils module."""

import unittest

from pytoolkit.crypto_utils import hash_bytes, hash_text, random_token


class TestCryptoUtils(unittest.TestCase):
    def test_hash_bytes_sha256(self):
        """Test hashing bytes with SHA256."""
        data = b"hello world"
        result = hash_bytes(data, algorithm="sha256")

        self.assertEqual(len(result), 64)  # SHA256 produces 64 hex characters
        self.assertIsInstance(result, str)
        # Verify deterministic hashing
        self.assertEqual(hash_bytes(data, algorithm="sha256"), result)

    def test_hash_bytes_sha3_256(self):
        """Test hashing bytes with SHA3-256."""
        data = b"test data"
        result = hash_bytes(data, algorithm="sha3_256")

        self.assertEqual(len(result), 64)
        self.assertIsInstance(result, str)

    def test_hash_bytes_blake2b(self):
        """Test hashing bytes with BLAKE2b."""
        data = b"test data"
        result = hash_bytes(data, algorithm="blake2b")

        self.assertEqual(len(result), 128)  # BLAKE2b produces 128 hex characters
        self.assertIsInstance(result, str)

    def test_hash_bytes_invalid_algorithm(self):
        """Test that invalid algorithm raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            hash_bytes(b"data", algorithm="invalid")  # type: ignore

        self.assertIn("Unsupported hash algorithm", str(cm.exception))

    def test_hash_text_default(self):
        """Test hashing text with default encoding."""
        text = "hello world"
        result = hash_text(text)

        self.assertEqual(len(result), 64)
        self.assertIsInstance(result, str)
        # Should match hashing the encoded bytes
        self.assertEqual(result, hash_bytes(text.encode("utf-8")))

    def test_hash_text_different_encodings(self):
        """Test hashing text with different encodings."""
        text = "café"
        result_utf8 = hash_text(text, encoding="utf-8")
        result_latin1 = hash_text(text, encoding="latin-1")

        # Different encodings should produce different hashes
        self.assertNotEqual(result_utf8, result_latin1)

    def test_random_token_default_length(self):
        """Test random token generation with default length."""
        token = random_token()

        self.assertEqual(len(token), 32)
        self.assertIsInstance(token, str)
        # Check that it's hexadecimal
        int(token, 16)  # Should not raise

    def test_random_token_custom_length(self):
        """Test random token generation with custom length."""
        lengths = [8, 16, 24, 64, 128]
        for length in lengths:
            token = random_token(length=length)
            self.assertEqual(len(token), length)

    def test_random_token_uniqueness(self):
        """Test that random tokens are unique."""
        tokens = [random_token() for _ in range(100)]
        # All tokens should be unique
        self.assertEqual(len(tokens), len(set(tokens)))

    def test_random_token_invalid_length(self):
        """Test that invalid length raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            random_token(length=0)

        self.assertIn("length must be positive", str(cm.exception))

        with self.assertRaises(ValueError):
            random_token(length=-5)


if __name__ == "__main__":
    unittest.main()
