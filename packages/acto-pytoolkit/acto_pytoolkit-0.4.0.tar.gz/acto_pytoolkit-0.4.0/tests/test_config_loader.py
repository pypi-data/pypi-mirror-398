import json
import os
import tempfile
import unittest

from pytoolkit.config_loader import ConfigLoader


class TestConfigLoader(unittest.TestCase):
    def test_json_loading(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            json_path = os.path.join(tmp_dir, "config.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump({"a": 1, "nested": {"b": 2}}, f)
            config = ConfigLoader(json_file=json_path)
            data = config.as_dict()
            self.assertEqual(data["a"], 1)
            self.assertEqual(data["nested.b"], 2)

    def test_env_override(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            json_path = os.path.join(tmp_dir, "config.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump({"KEY": "from_json"}, f)
            os.environ["KEY"] = "from_env"
            try:
                config = ConfigLoader(json_file=json_path)
                self.assertEqual(config.get("KEY"), "from_env")
            finally:
                del os.environ["KEY"]


if __name__ == "__main__":
    unittest.main()
