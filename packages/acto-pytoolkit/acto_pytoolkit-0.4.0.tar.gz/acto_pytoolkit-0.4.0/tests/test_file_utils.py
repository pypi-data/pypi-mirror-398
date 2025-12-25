"""Tests for the file_utils module."""

import os
import tempfile
import unittest

from pytoolkit.file_utils import (
    atomic_write,
    file_hash,
    read_json,
    read_text,
    safe_delete,
    write_json,
    write_text,
)


class TestFileUtils(unittest.TestCase):
    def test_read_write_text(self):
        """Test reading and writing text files."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            filepath = f.name

        try:
            content = "Hello World!\nThis is a test."
            write_text(filepath, content)

            result = read_text(filepath)
            self.assertEqual(result, content)
        finally:
            safe_delete(filepath)

    def test_read_write_json(self):
        """Test reading and writing JSON files."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            filepath = f.name

        try:
            data = {"name": "Alice", "age": 30, "items": [1, 2, 3]}
            write_json(filepath, data)

            result = read_json(filepath)
            self.assertEqual(result, data)
        finally:
            safe_delete(filepath)

    def test_atomic_write(self):
        """Test atomic write operation."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            filepath = f.name

        try:
            content = "Atomically written content"
            atomic_write(filepath, content)

            with open(filepath) as f:
                result = f.read()

            self.assertEqual(result, content)
        finally:
            safe_delete(filepath)

    def test_file_hash(self):
        """Test file hashing."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("test content")
            filepath = f.name

        try:
            hash1 = file_hash(filepath, algorithm="sha256")
            hash2 = file_hash(filepath, algorithm="sha256")

            # Same file should produce same hash
            self.assertEqual(hash1, hash2)
            self.assertEqual(len(hash1), 64)  # SHA256 produces 64 hex chars
        finally:
            safe_delete(filepath)

    def test_safe_delete_existing_file(self):
        """Test safe_delete on existing file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            filepath = f.name

        self.assertTrue(os.path.exists(filepath))
        safe_delete(filepath)
        self.assertFalse(os.path.exists(filepath))

    def test_safe_delete_missing_file(self):
        """Test safe_delete on missing file (should not raise)."""
        filepath = "/tmp/nonexistent_file_xyz123.txt"

        # Should not raise an exception
        safe_delete(filepath)

    def test_write_text_with_encoding(self):
        """Test writing text with specific encoding."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            filepath = f.name

        try:
            content = "Café ☕"
            write_text(filepath, content, encoding="utf-8")

            result = read_text(filepath, encoding="utf-8")
            self.assertEqual(result, content)
        finally:
            safe_delete(filepath)


if __name__ == "__main__":
    unittest.main()
