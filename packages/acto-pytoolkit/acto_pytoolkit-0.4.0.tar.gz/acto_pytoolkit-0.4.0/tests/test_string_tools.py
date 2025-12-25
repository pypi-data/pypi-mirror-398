import unittest

from pytoolkit.string_tools import (
    extract_numbers,
    random_string,
    slugify,
    to_camel_case,
    to_snake_case,
    truncate,
)


class TestStringTools(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(slugify("Hello World"), "hello-world")
        self.assertEqual(slugify("Already-slug"), "already-slug")

    def test_to_snake_case(self):
        self.assertEqual(to_snake_case("CamelCase"), "camel_case")
        self.assertEqual(to_snake_case("camelCaseValue"), "camel_case_value")

    def test_to_camel_case(self):
        self.assertEqual(to_camel_case("snake_case"), "SnakeCase")
        self.assertEqual(to_camel_case("already Camel"), "AlreadyCamel")

    def test_random_string(self):
        s = random_string(10)
        self.assertEqual(len(s), 10)

    def test_extract_numbers(self):
        nums = extract_numbers("Value is 10 and 3.5")
        self.assertEqual(nums, [10.0, 3.5])

    def test_truncate(self):
        self.assertEqual(truncate("abcdef", 10), "abcdef")
        self.assertEqual(truncate("abcdef", 5), "ab...")
        with self.assertRaises(ValueError):
            truncate("test", 3, suffix="....")


if __name__ == "__main__":
    unittest.main()
