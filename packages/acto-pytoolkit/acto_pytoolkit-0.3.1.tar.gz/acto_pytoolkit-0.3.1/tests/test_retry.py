"""Tests for the retry module."""
import time
import unittest
from unittest.mock import Mock

from pytoolkit.retry import retry


class TestRetry(unittest.TestCase):
    def test_retry_success_first_attempt(self):
        """Test successful execution on first attempt."""
        mock_func = Mock(return_value="success")
        decorated = retry(max_attempts=3)(mock_func)
        
        result = decorated()
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 1)

    def test_retry_success_after_failures(self):
        """Test successful execution after some failures."""
        mock_func = Mock(side_effect=[ValueError("error"), ValueError("error"), "success"])
        mock_func.__name__ = "mock_func"
        decorated = retry(max_attempts=3, initial_delay=0.01, jitter=0)(mock_func)
        
        result = decorated()
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 3)

    def test_retry_max_attempts_exceeded(self):
        """Test that exception is raised after max attempts."""
        mock_func = Mock(side_effect=ValueError("persistent error"))
        mock_func.__name__ = "mock_func"
        decorated = retry(max_attempts=3, initial_delay=0.01, jitter=0)(mock_func)
        
        with self.assertRaises(ValueError) as cm:
            decorated()
        
        self.assertIn("persistent error", str(cm.exception))
        self.assertEqual(mock_func.call_count, 3)

    def test_retry_specific_exceptions(self):
        """Test retrying only specific exceptions."""
        mock_func = Mock(side_effect=TypeError("wrong type"))
        decorated = retry(exceptions=(ValueError,), max_attempts=3)(mock_func)
        
        with self.assertRaises(TypeError):
            decorated()
        
        # Should fail immediately since TypeError is not in the retry list
        self.assertEqual(mock_func.call_count, 1)

    def test_retry_with_backoff(self):
        """Test exponential backoff."""
        mock_func = Mock(side_effect=[ValueError("error"), ValueError("error"), "success"])
        mock_func.__name__ = "mock_func"
        
        start_time = time.time()
        decorated = retry(
            max_attempts=3,
            initial_delay=0.1,
            backoff_factor=2.0,
            jitter=0
        )(mock_func)
        result = decorated()
        elapsed = time.time() - start_time
        
        self.assertEqual(result, "success")
        # First retry: 0.1s, second retry: 0.2s = ~0.3s total
        self.assertGreater(elapsed, 0.25)

    def test_retry_with_args_kwargs(self):
        """Test retry with function arguments."""
        mock_func = Mock(return_value="result")
        decorated = retry(max_attempts=2)(mock_func)
        
        result = decorated("arg1", "arg2", key="value")
        
        self.assertEqual(result, "result")
        mock_func.assert_called_once_with("arg1", "arg2", key="value")

    def test_retry_preserves_function_metadata(self):
        """Test that functools.wraps preserves function metadata."""
        @retry(max_attempts=3)
        def example_function():
            """Example docstring."""
            return "result"
        
        self.assertEqual(example_function.__name__, "example_function")
        self.assertEqual(example_function.__doc__, "Example docstring.")


if __name__ == "__main__":
    unittest.main()

