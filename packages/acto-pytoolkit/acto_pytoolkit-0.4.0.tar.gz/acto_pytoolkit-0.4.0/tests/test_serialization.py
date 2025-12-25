"""Tests for the serialization module."""

import json
import os
import tempfile
import unittest

from pytoolkit import serialization


class TestSerialization(unittest.TestCase):
    def test_load_json(self):
        """Test loading JSON from file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump({"key": "value", "number": 42}, f)
            json_file = f.name

        try:
            data = serialization.load_json(json_file)
            self.assertEqual(data["key"], "value")
            self.assertEqual(data["number"], 42)
        finally:
            os.remove(json_file)

    def test_save_json(self):
        """Test saving JSON to file."""
        data = {"name": "test", "items": [1, 2, 3]}

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json_file = f.name

        try:
            serialization.save_json(json_file, data)

            # Read back and verify
            with open(json_file) as f:
                loaded = json.load(f)

            self.assertEqual(loaded, data)
        finally:
            if os.path.exists(json_file):
                os.remove(json_file)

    def test_load_yaml(self):
        """Test loading YAML from file."""
        yaml_content = """
        name: test
        values:
          - one
          - two
          - three
        """

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as f:
            f.write(yaml_content)
            yaml_file = f.name

        try:
            data = serialization.load_yaml(yaml_file)
            self.assertEqual(data["name"], "test")
            self.assertEqual(data["values"], ["one", "two", "three"])
        finally:
            os.remove(yaml_file)

    def test_save_yaml(self):
        """Test saving YAML to file."""
        data = {"name": "test", "count": 5}

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as f:
            yaml_file = f.name

        try:
            serialization.save_yaml(yaml_file, data)

            # Read back and verify
            loaded = serialization.load_yaml(yaml_file)
            self.assertEqual(loaded, data)
        finally:
            if os.path.exists(yaml_file):
                os.remove(yaml_file)


if __name__ == "__main__":
    unittest.main()
