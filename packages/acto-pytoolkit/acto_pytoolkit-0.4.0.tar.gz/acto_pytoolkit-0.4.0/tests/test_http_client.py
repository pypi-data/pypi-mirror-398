"""Tests for the http_client module."""

import unittest
from unittest.mock import Mock, patch

from pytoolkit.http_client import HttpClient


class TestHttpClient(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.base_url = "https://api.example.com"
        self.client = HttpClient(base_url=self.base_url, timeout=5.0)

    def tearDown(self):
        """Clean up after tests."""
        self.client.close()

    @patch("pytoolkit.http_client.requests.Session.request")
    def test_get_request(self, mock_request):
        """Test GET request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        self.client.get("/users")

        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "GET")
        self.assertIn("api.example.com/users", args[1])

    @patch("pytoolkit.http_client.requests.Session.request")
    def test_post_request(self, mock_request):
        """Test POST request with JSON data."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_request.return_value = mock_response

        data = {"name": "John"}
        self.client.post("/users", json=data)

        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "POST")
        self.assertEqual(kwargs.get("json"), data)

    @patch("pytoolkit.http_client.requests.Session.request")
    def test_put_request(self, mock_request):
        """Test PUT request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        self.client.put("/users/1", json={"name": "Jane"})

        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "PUT")

    @patch("pytoolkit.http_client.requests.Session.request")
    def test_patch_request(self, mock_request):
        """Test PATCH request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        self.client.patch("/users/1", json={"email": "jane@example.com"})

        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "PATCH")

    @patch("pytoolkit.http_client.requests.Session.request")
    def test_delete_request(self, mock_request):
        """Test DELETE request."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_request.return_value = mock_response

        self.client.delete("/users/1")

        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "DELETE")

    def test_json_parsing(self):
        """Test JSON response parsing."""
        mock_response = Mock()
        mock_response.json.return_value = {"key": "value"}

        result = HttpClient.json(mock_response)
        self.assertEqual(result, {"key": "value"})

    def test_json_parsing_error(self):
        """Test JSON parsing error handling."""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")

        with self.assertRaises(ValueError) as cm:
            HttpClient.json(mock_response)
        self.assertIn("Failed to decode JSON", str(cm.exception))

    def test_context_manager(self):
        """Test context manager usage."""
        with HttpClient(base_url=self.base_url) as client:
            self.assertIsNotNone(client.session)
        # Session should be closed after context

    def test_default_headers(self):
        """Test setting default headers."""
        headers = {"Authorization": "Bearer token123"}
        client = HttpClient(base_url=self.base_url, default_headers=headers)

        self.assertEqual(client.session.headers["Authorization"], "Bearer token123")
        client.close()

    def test_basic_auth(self):
        """Test basic authentication."""
        auth = ("user", "pass")
        client = HttpClient(base_url=self.base_url, auth=auth)

        self.assertEqual(client.session.auth, auth)
        client.close()


if __name__ == "__main__":
    unittest.main()
