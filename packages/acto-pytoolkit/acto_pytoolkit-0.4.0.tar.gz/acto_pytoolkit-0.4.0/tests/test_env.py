"""Tests for the env module."""

import os
import unittest

from pytoolkit.env import Environment, get_environment


class TestEnvironment(unittest.TestCase):
    def test_environment_default(self):
        """Test Environment with default values."""
        env = Environment()

        self.assertEqual(env.name, "development")
        self.assertTrue(env.is_development)
        self.assertFalse(env.is_staging)
        self.assertFalse(env.is_production)

    def test_environment_production(self):
        """Test Environment with production."""
        env = Environment(name="production")

        self.assertEqual(env.name, "production")
        self.assertTrue(env.is_production)
        self.assertFalse(env.is_development)
        self.assertFalse(env.is_staging)

    def test_environment_staging(self):
        """Test Environment with staging."""
        env = Environment(name="staging")

        self.assertEqual(env.name, "staging")
        self.assertTrue(env.is_staging)
        self.assertFalse(env.is_development)
        self.assertFalse(env.is_production)

    def test_environment_aliases(self):
        """Test environment name aliases."""
        dev_env = Environment(name="dev")
        self.assertTrue(dev_env.is_development)

        stage_env = Environment(name="stage")
        self.assertTrue(stage_env.is_staging)

        prod_env = Environment(name="prod")
        self.assertTrue(prod_env.is_production)

    def test_get_environment_from_env_var(self):
        """Test get_environment from environment variable."""
        os.environ["APP_ENV"] = "production"

        try:
            env = get_environment()
            self.assertEqual(env.name, "production")
            self.assertTrue(env.is_production)
        finally:
            os.environ.pop("APP_ENV", None)

    def test_get_environment_custom_var(self):
        """Test get_environment with custom variable name."""
        os.environ["CUSTOM_ENV"] = "staging"

        try:
            env = get_environment(var_name="CUSTOM_ENV")
            self.assertEqual(env.name, "staging")
            self.assertTrue(env.is_staging)
        finally:
            os.environ.pop("CUSTOM_ENV", None)

    def test_get_environment_default_fallback(self):
        """Test get_environment falls back to default."""
        # Make sure APP_ENV is not set
        old_value = os.environ.pop("APP_ENV", None)

        try:
            env = get_environment(default="testing")
            self.assertEqual(env.name, "testing")
        finally:
            if old_value:
                os.environ["APP_ENV"] = old_value

    def test_environment_immutable(self):
        """Test that Environment is immutable (frozen dataclass)."""
        env = Environment(name="production")

        # FrozenInstanceError is a subclass of AttributeError
        with self.assertRaises(AttributeError):
            env.name = "development"  # type: ignore


if __name__ == "__main__":
    unittest.main()
