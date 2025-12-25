"""Tests for the math_tools module."""
import unittest

from pytoolkit.math_tools import (
    moving_average,
    normalize,
    percentage_change,
    scale_value,
)


class TestMathTools(unittest.TestCase):
    def test_moving_average_basic(self):
        """Test basic moving average calculation."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = moving_average(values, window=3)
        
        expected = [1.0, 1.5, 2.0, 3.0, 4.0]
        self.assertEqual(result, expected)

    def test_moving_average_window_one(self):
        """Test moving average with window size 1."""
        values = [1.0, 2.0, 3.0]
        result = moving_average(values, window=1)
        
        self.assertEqual(result, values)

    def test_moving_average_large_window(self):
        """Test moving average with window larger than data."""
        values = [1.0, 2.0, 3.0]
        result = moving_average(values, window=10)
        
        expected = [1.0, 1.5, 2.0]
        self.assertEqual(result, expected)

    def test_moving_average_invalid_window(self):
        """Test moving average with invalid window."""
        with self.assertRaises(ValueError):
            moving_average([1.0, 2.0], window=0)
        
        with self.assertRaises(ValueError):
            moving_average([1.0, 2.0], window=-1)

    def test_normalize_basic(self):
        """Test basic normalization."""
        values = [0.0, 5.0, 10.0]
        result = normalize(values)
        
        expected = [0.0, 0.5, 1.0]
        self.assertEqual(result, expected)

    def test_normalize_same_values(self):
        """Test normalizing identical values."""
        values = [5.0, 5.0, 5.0]
        result = normalize(values)
        
        expected = [0.5, 0.5, 0.5]
        self.assertEqual(result, expected)

    def test_normalize_empty(self):
        """Test normalizing empty list."""
        result = normalize([])
        self.assertEqual(result, [])

    def test_normalize_negative_values(self):
        """Test normalizing negative values."""
        values = [-10.0, 0.0, 10.0]
        result = normalize(values)
        
        expected = [0.0, 0.5, 1.0]
        self.assertEqual(result, expected)

    def test_percentage_change_increase(self):
        """Test percentage change for increase."""
        result = percentage_change(100.0, 110.0)
        self.assertAlmostEqual(result, 10.0)

    def test_percentage_change_decrease(self):
        """Test percentage change for decrease."""
        result = percentage_change(100.0, 90.0)
        self.assertAlmostEqual(result, -10.0)

    def test_percentage_change_no_change(self):
        """Test percentage change when values are equal."""
        result = percentage_change(100.0, 100.0)
        self.assertAlmostEqual(result, 0.0)

    def test_percentage_change_zero_old(self):
        """Test percentage change with zero old value."""
        with self.assertRaises(ZeroDivisionError):
            percentage_change(0.0, 100.0)

    def test_scale_value_basic(self):
        """Test basic value scaling."""
        # Scale 5 from [0, 10] to [0, 100]
        result = scale_value(5.0, 0.0, 10.0, 0.0, 100.0)
        self.assertAlmostEqual(result, 50.0)

    def test_scale_value_different_ranges(self):
        """Test scaling between different ranges."""
        # Scale 0 from [0, 100] to [50, 150]
        result = scale_value(0.0, 0.0, 100.0, 50.0, 150.0)
        self.assertAlmostEqual(result, 50.0)
        
        # Scale 100 from [0, 100] to [50, 150]
        result = scale_value(100.0, 0.0, 100.0, 50.0, 150.0)
        self.assertAlmostEqual(result, 150.0)

    def test_scale_value_equal_range(self):
        """Test scaling with equal old_min and old_max."""
        with self.assertRaises(ZeroDivisionError):
            scale_value(5.0, 10.0, 10.0, 0.0, 100.0)


if __name__ == "__main__":
    unittest.main()

