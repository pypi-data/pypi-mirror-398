"""Tests for the timer module."""

import logging
import time
import unittest
from io import StringIO

from pytoolkit.timer import Timer, time_function


class TestTimer(unittest.TestCase):
    def test_timer_context_manager(self):
        """Test Timer as context manager."""
        with Timer("test_operation") as timer:
            time.sleep(0.05)

        self.assertGreater(timer.duration, 0.04)
        self.assertLess(timer.duration, 0.3)  # Increased tolerance for system overhead

    def test_timer_with_logger(self):
        """Test Timer with custom logger."""
        # Create a string buffer to capture log output
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger("test_timer")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        with Timer("logged_operation", logger=logger):
            time.sleep(0.01)

        log_output = log_stream.getvalue()
        self.assertIn("logged_operation", log_output)
        self.assertIn("took", log_output)
        self.assertIn("seconds", log_output)

    def test_timer_as_decorator(self):
        """Test Timer as decorator."""

        @Timer("decorated_function")
        def slow_function():
            time.sleep(0.01)
            return "result"

        result = slow_function()
        self.assertEqual(result, "result")

    def test_time_function_decorator(self):
        """Test time_function decorator."""
        call_count = 0

        @time_function()
        def example_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y

        result = example_function(2, 3)

        self.assertEqual(result, 5)
        self.assertEqual(call_count, 1)

    def test_time_function_with_label(self):
        """Test time_function with custom label."""
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger("test_time_func")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        @time_function(label="custom_label", logger=logger)
        def example_function():
            time.sleep(0.01)
            return "done"

        result = example_function()

        self.assertEqual(result, "done")
        log_output = log_stream.getvalue()
        self.assertIn("custom_label", log_output)

    def test_time_function_preserves_metadata(self):
        """Test that time_function preserves function metadata."""

        @time_function()
        def documented_function():
            """This function has documentation."""
            return True

        self.assertEqual(documented_function.__name__, "documented_function")
        self.assertEqual(documented_function.__doc__, "This function has documentation.")


if __name__ == "__main__":
    unittest.main()
