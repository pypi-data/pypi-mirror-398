import unittest

from pytoolkit.validators import (
    is_email,
    is_url,
    is_uuid,
    has_extension,
    is_ipv4,
    is_ipv6,
    min_length,
    max_length,
)


class TestValidators(unittest.TestCase):
    def test_email(self):
        self.assertTrue(is_email("user@example.com"))
        self.assertFalse(is_email("invalid"))

    def test_url(self):
        self.assertTrue(is_url("https://example.com"))
        self.assertFalse(is_url("ftp://example.com"))

    def test_uuid(self):
        self.assertTrue(is_uuid("12345678-1234-5678-1234-567812345678"))
        self.assertFalse(is_uuid("not-a-uuid"))

    def test_extension(self):
        self.assertTrue(has_extension("file.txt", ".txt"))
        self.assertFalse(has_extension("file.txt", ".json"))

    def test_ip(self):
        self.assertTrue(is_ipv4("192.168.0.1"))
        self.assertFalse(is_ipv4("999.999.999.999"))
        self.assertTrue(is_ipv6("::1"))
        self.assertFalse(is_ipv6("not-an-ip"))

    def test_length(self):
        self.assertTrue(min_length("abc", 2))
        self.assertFalse(min_length("a", 2))
        self.assertTrue(max_length("abc", 3))
        self.assertFalse(max_length("abcd", 3))


if __name__ == "__main__":
    unittest.main()
