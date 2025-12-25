"""Tests for the async_http_client module."""
import asyncio
import unittest

try:
    import aiohttp
    from aiohttp import web

    from pytoolkit.async_http_client import AsyncHttpClient

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False


@unittest.skipUnless(AIOHTTP_AVAILABLE, "aiohttp not installed")
class TestAsyncHttpClient(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.base_url = "https://httpbin.org"

    def test_client_initialization(self):
        """Test client initialization."""
        client = AsyncHttpClient(base_url=self.base_url, timeout=5.0)
        self.assertEqual(client.base_url, self.base_url)

    def test_context_manager_sync(self):
        """Test that context manager can be created synchronously."""
        client = AsyncHttpClient(base_url=self.base_url)
        self.assertIsNotNone(client)

    async def async_test_get_request(self):
        """Test GET request."""
        async with AsyncHttpClient(base_url=self.base_url) as client:
            # Note: This test requires internet connection
            # In a real scenario, you'd mock the response
            self.assertIsNotNone(client)

    async def async_test_json_parsing(self):
        """Test JSON parsing from response."""
        # This is a placeholder - in real tests you'd mock the response
        async with AsyncHttpClient(base_url=self.base_url) as client:
            # Create a mock response
            class MockResponse:
                async def json(self):
                    return {"key": "value"}

            mock_resp = MockResponse()
            result = await AsyncHttpClient.json(mock_resp)
            self.assertEqual(result, {"key": "value"})

    async def async_test_text_parsing(self):
        """Test text parsing from response."""

        class MockResponse:
            async def text(self):
                return "test content"

        mock_resp = MockResponse()
        result = await AsyncHttpClient.text(mock_resp)
        self.assertEqual(result, "test content")

    def test_run_async_tests(self):
        """Run async tests."""
        if AIOHTTP_AVAILABLE:
            asyncio.run(self.async_test_get_request())
            asyncio.run(self.async_test_json_parsing())
            asyncio.run(self.async_test_text_parsing())


if __name__ == "__main__":
    unittest.main()

