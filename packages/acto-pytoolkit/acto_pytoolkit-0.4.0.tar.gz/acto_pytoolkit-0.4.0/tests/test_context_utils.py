"""Tests for the context_utils module."""

import unittest

from pytoolkit import context_utils


class TestContextUtils(unittest.TestCase):
    def test_get_nested_value(self):
        """Test getting nested values from dictionary."""
        data = {"user": {"name": "John", "address": {"city": "New York", "zip": "10001"}}}

        result = context_utils.get_nested(data, "user.address.city")
        self.assertEqual(result, "New York")

    def test_get_nested_default(self):
        """Test getting nested value with default."""
        data = {"user": {"name": "John"}}

        result = context_utils.get_nested(data, "user.email", default="no-email")
        self.assertEqual(result, "no-email")

    def test_set_nested_value(self):
        """Test setting nested values in dictionary."""
        data = {}

        context_utils.set_nested(data, "user.profile.name", "Alice")

        self.assertEqual(data["user"]["profile"]["name"], "Alice")

    def test_set_nested_existing_path(self):
        """Test setting value in existing nested path."""
        data = {"user": {"name": "John"}}

        context_utils.set_nested(data, "user.email", "john@example.com")

        self.assertEqual(data["user"]["email"], "john@example.com")
        self.assertEqual(data["user"]["name"], "John")  # Original value preserved

    def test_flatten_dict(self):
        """Test flattening nested dictionary."""
        data = {"user": {"name": "John", "address": {"city": "NYC"}}, "count": 5}

        flat = context_utils.flatten_dict(data)

        self.assertEqual(flat["user.name"], "John")
        self.assertEqual(flat["user.address.city"], "NYC")
        self.assertEqual(flat["count"], 5)

    def test_unflatten_dict(self):
        """Test unflattening a flat dictionary."""
        flat = {"user.name": "John", "user.address.city": "NYC", "count": 5}

        nested = context_utils.unflatten_dict(flat)

        self.assertEqual(nested["user"]["name"], "John")
        self.assertEqual(nested["user"]["address"]["city"], "NYC")
        self.assertEqual(nested["count"], 5)


if __name__ == "__main__":
    unittest.main()
