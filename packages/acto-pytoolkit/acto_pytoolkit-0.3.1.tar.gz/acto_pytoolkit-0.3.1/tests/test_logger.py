"""Tests for the logger module."""
import logging
import os
import tempfile
import unittest

from pytoolkit.logger import get_logger, configure_from_env


class TestLogger(unittest.TestCase):
    def test_get_logger_basic(self):
        """Test basic logger creation."""
        logger = get_logger("test_logger")
        
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "test_logger")
        self.assertEqual(logger.level, logging.INFO)

    def test_get_logger_custom_level(self):
        """Test logger with custom level."""
        logger = get_logger("custom_level_logger", level=logging.DEBUG)
        
        self.assertEqual(logger.level, logging.DEBUG)

    def test_get_logger_with_file(self):
        """Test logger with file output."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
            log_file = f.name
        
        try:
            logger = get_logger("file_logger", to_file=log_file)
            logger.info("Test message")
            
            # Close all handlers to release the file (important on Windows)
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
            
            # Check that file was created and contains the message
            with open(log_file, "r") as f:
                content = f.read()
            
            self.assertIn("Test message", content)
            self.assertIn("INFO", content)
        finally:
            if os.path.exists(log_file):
                try:
                    os.remove(log_file)
                except PermissionError:
                    # On Windows, file might still be locked
                    pass

    def test_get_logger_without_colors(self):
        """Test logger without color formatting."""
        logger = get_logger("no_color_logger", with_colors=False)
        
        # Logger should still work
        self.assertIsInstance(logger, logging.Logger)

    def test_configure_from_env_default(self):
        """Test configure_from_env with default level."""
        # Make sure LOG_LEVEL is not set
        old_value = os.environ.pop("LOG_LEVEL", None)
        
        try:
            logger = configure_from_env()
            self.assertEqual(logger.level, logging.INFO)
        finally:
            if old_value:
                os.environ["LOG_LEVEL"] = old_value

    def test_configure_from_env_debug(self):
        """Test configure_from_env with DEBUG level."""
        os.environ["LOG_LEVEL"] = "DEBUG"
        
        try:
            logger = configure_from_env()
            self.assertEqual(logger.level, logging.DEBUG)
        finally:
            os.environ.pop("LOG_LEVEL", None)

    def test_configure_from_env_invalid(self):
        """Test configure_from_env with invalid level falls back to default."""
        os.environ["LOG_LEVEL"] = "INVALID"
        
        try:
            logger = configure_from_env(default_level=logging.WARNING)
            self.assertEqual(logger.level, logging.WARNING)
        finally:
            os.environ.pop("LOG_LEVEL", None)

    def test_logger_no_duplicate_handlers(self):
        """Test that getting the same logger twice doesn't add duplicate handlers."""
        logger1 = get_logger("duplicate_test")
        handler_count1 = len(logger1.handlers)
        
        logger2 = get_logger("duplicate_test")
        handler_count2 = len(logger2.handlers)
        
        # Should have the same number of handlers
        self.assertEqual(handler_count1, handler_count2)


if __name__ == "__main__":
    unittest.main()

