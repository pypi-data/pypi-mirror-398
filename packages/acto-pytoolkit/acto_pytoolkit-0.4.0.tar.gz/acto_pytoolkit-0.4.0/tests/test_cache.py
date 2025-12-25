import time
import unittest

from pytoolkit.cache import SimpleCache, cached


class TestSimpleCache(unittest.TestCase):
    def test_set_get(self):
        cache = SimpleCache()
        cache.set("a", 1)
        self.assertEqual(cache.get("a"), 1)

    def test_ttl(self):
        cache = SimpleCache()
        cache.set("a", 1, ttl=0.1)
        self.assertEqual(cache.get("a"), 1)
        time.sleep(0.2)
        self.assertIsNone(cache.get("a"))

    def test_cached_decorator_handles_none(self):
        calls = {"count": 0}

        @cached(ttl=1.0)
        def maybe_none(x):
            calls["count"] += 1
            return None if x == 0 else x

        self.assertIsNone(maybe_none(0))
        self.assertIsNone(maybe_none(0))
        self.assertEqual(calls["count"], 1)


if __name__ == "__main__":
    unittest.main()
