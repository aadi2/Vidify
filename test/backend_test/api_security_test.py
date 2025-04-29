import unittest
import sys
import subprocess
import requests
import time
import os
import shutil

BASE_URL = "http://127.0.0.1:8001"
API_KEY = "vid-xyz-123456789-vidify-secure-key"  # Same key as defined in app.py


class ApiSecurityTest(unittest.TestCase):
    def setUp(self):
        # Use a valid YouTube URL for testing
        self.valid_url = "https://www.youtube.com/watch?v=W86cTIoMv2U"
        self.keyword = "test"

        # Start the Flask app
        self.process = subprocess.Popen(
            [sys.executable, "src/backend/app.py"], stdout=sys.stdout, stderr=sys.stderr
        )

        # Wait for the server to start
        for _ in range(15):
            try:
                response = requests.get(f"{BASE_URL}/health")
                if response.status_code == 200:
                    break
            except requests.ConnectionError:
                time.sleep(1)
        else:
            raise RuntimeError("Flask server failed to start.")

    def test_api_access_with_valid_key(self):
        """Test that requests with valid API key succeed"""
        # Test transcript_search endpoint
        response = requests.get(
            f"{BASE_URL}/transcript_search?yt_url={self.valid_url}&keyword={self.keyword}",
            headers={"X-API-Key": API_KEY},
        )
        # The actual status code depends on whether transcript is found,
        # but it should not be 401 Unauthorized
        self.assertNotEqual(response.status_code, 401)
        self.assertNotIn("unauthorized", response.text.lower())

        # Test object_search endpoint
        response = requests.get(
            f"{BASE_URL}/object_search?yt_url={self.valid_url}&keyword={self.keyword}",
            headers={"X-API-Key": API_KEY},
        )
        # The actual status code depends on implementation status,
        # but it should not be 401 Unauthorized
        self.assertNotEqual(response.status_code, 401)
        self.assertNotIn("unauthorized", response.text.lower())

    def test_api_access_with_invalid_key(self):
        """Test that requests with invalid API key are rejected"""
        # Test transcript_search endpoint with wrong key
        response = requests.get(
            f"{BASE_URL}/transcript_search?yt_url={self.valid_url}&keyword={self.keyword}",
            headers={"X-API-Key": "wrong-key"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("unauthorized", response.text.lower())

        # Test object_search endpoint with wrong key
        response = requests.get(
            f"{BASE_URL}/object_search?yt_url={self.valid_url}&keyword={self.keyword}",
            headers={"X-API-Key": "wrong-key"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("unauthorized", response.text.lower())

    def test_api_access_without_key(self):
        """Test that requests without API key are rejected"""
        # Test transcript_search endpoint without key
        response = requests.get(
            f"{BASE_URL}/transcript_search?yt_url={self.valid_url}&keyword={self.keyword}"
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("unauthorized", response.text.lower())

        # Test object_search endpoint without key
        response = requests.get(
            f"{BASE_URL}/object_search?yt_url={self.valid_url}&keyword={self.keyword}"
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("unauthorized", response.text.lower())

    def tearDown(self):
        # Stop the Flask app
        self.process.terminate()
        self.process.wait()

        # Clean up
        if os.path.exists("temp"):
            shutil.rmtree("temp")


if __name__ == "__main__":
    unittest.main(testRunner=unittest.TextTestRunner(stream=sys.stdout))
