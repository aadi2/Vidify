import unittest
import sys
import subprocess
import requests
import time
import os
import pytest
import shutil
from unittest.mock import patch

BASE_URL = "http://127.0.0.1:8001"

##############################################
# General App Tests (TestSuite)
##############################################

class TestSuite(unittest.TestCase):
    def setUp(self):
        self.invalid_url = "invalid_url"
        self.no_transcript_url = "https://www.youtube.com/watch?v=sD9gTAFDq40"
        self.valid_url = "https://www.youtube.com/watch?v=W86cTIoMv2U"

        self.process = subprocess.Popen(
            [sys.executable, "src/backend/app.py"],
            stdout=sys.stdout, stderr=sys.stderr
        )

        for _ in range(6):
            try:
                response = requests.get(f"{BASE_URL}/health")
                if response.status_code == 200:
                    break
            except requests.ConnectionError:
                time.sleep(1)
        else:
            raise RuntimeError("Flask server failed to start.")

    @pytest.mark.skip(reason="Have to fix cookies first. Avoiding blocking the development.")
    def test_app(self):
        with self.subTest(key=self.invalid_url):
            response = requests.get(f"{BASE_URL}/?hash_id={self.invalid_url}")
            print(response)
            self.assertEqual(response.status_code, 404)
            self.assertIn("not able to download the video", response.text.lower())

        with self.subTest(key=self.no_transcript_url):
            response = requests.get(f"{BASE_URL}/?hash_id={self.no_transcript_url}")
            self.assertEqual(response.status_code, 404)
            self.assertIn("not able to fetch transcript", response.text.lower())

        with self.subTest(key=self.valid_url):
            response = requests.get(f"{BASE_URL}/?hash_id={self.valid_url}")
            self.assertEqual(response.status_code, 200)
            self.assertIn("video and transcript downloaded successfully", response.text.lower())

    def tearDown(self):
        self.process.terminate()
        self.process.wait()
        del self.invalid_url
        del self.no_transcript_url
        del self.valid_url
        if os.path.exists("temp"):
            shutil.rmtree("temp")

##############################################
# Video Tests (VideoTestSuite)
##############################################

class VideoTestSuite(unittest.TestCase):
    def setUp(self):
        # Enable TEST_MODE to skip auth checks in app.py
        os.environ["TEST_MODE"] = "true"

        self.invalid_domain_url = "http://example.com/watch?v=abc123"  # Non-YouTube domain
        self.malformed_url = "invalid_url"  # Not even a valid scheme or domain
        self.no_transcript_url = "https://www.youtube.com/watch?v=sD9gTAFDq40"  # Might not have transcript
        self.valid_url = "https://www.youtube.com/watch?v=W86cTIoMv2U"  # Known to have transcript

        self.process = subprocess.Popen(
            [sys.executable, "src/backend/app.py"],
            stdout=sys.stdout, stderr=sys.stderr
        )

        for _ in range(6):
            try:
                response = requests.get(f"{BASE_URL}/health")
                if response.status_code == 200:
                    break
            except requests.ConnectionError:
                time.sleep(1)
        else:
            raise RuntimeError("Flask server failed to start.")

    def test_non_youtube_domain(self):
        """Expect 400 for non-YouTube domain (domain whitelisting)."""
        response = requests.get(f"{BASE_URL}/?hash_id={self.invalid_domain_url}")
        self.assertEqual(response.status_code, 400)
        self.assertIn("invalid video url", response.text.lower())

    def test_malformed_url(self):
        """Expect 400 for a completely invalid/malformed URL."""
        response = requests.get(f"{BASE_URL}/?hash_id={self.malformed_url}")
        self.assertEqual(response.status_code, 400)
        self.assertIn("invalid video url", response.text.lower())

    def test_no_transcript_url(self):
        """If the video doesn't have an English transcript, expect 404."""
        response = requests.get(f"{BASE_URL}/?hash_id={self.no_transcript_url}")
        self.assertEqual(response.status_code, 404)
        self.assertIn("not able to fetch transcript", response.text.lower())

    def test_valid_url(self):
        """A valid YouTube URL should return 200 with a success message."""
        response = requests.get(f"{BASE_URL}/?hash_id={self.valid_url}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("video and transcript downloaded successfully", response.text.lower())

    def test_rate_limit_exceeded(self):
        """
        Make multiple requests to the dedicated rate limit test endpoint 
        to confirm that the rate limiting returns a 429 on exceeding the threshold.
        """
        final_response = None
        # Assuming /test-rate-limit endpoint exists and is limited to 3 per minute.
        for _ in range(4):
            final_response = requests.get(f"{BASE_URL}/test-rate-limit")
        self.assertEqual(final_response.status_code, 429)
        self.assertIn("too many requests", final_response.text.lower())

    def tearDown(self):
        self.process.terminate()
        self.process.wait()
        if os.path.exists("temp"):
            shutil.rmtree("temp")

##############################################
# Auth Tests (AuthTestSuite)
##############################################

class AuthTestSuite(unittest.TestCase):
    def setUp(self):
        # Ensure TEST_MODE is off so auth is enforced
        if "TEST_MODE" in os.environ:
            del os.environ["TEST_MODE"]

        self.process = subprocess.Popen(
            [sys.executable, "src/backend/app.py"],
            stdout=sys.stdout, stderr=sys.stderr
        )

        for _ in range(6):
            try:
                response = requests.get(f"{BASE_URL}/health")
                if response.status_code == 200:
                    break
            except requests.ConnectionError:
                time.sleep(1)
        else:
            raise RuntimeError("Flask server failed to start.")

    def test_unauthorized_no_token(self):
        """Ensure that requests without an auth token return 401 Unauthorized."""
        response = requests.get(f"{BASE_URL}/?hash_id=invalid_url")
        self.assertEqual(response.status_code, 401)
        self.assertIn("unauthorized", response.text.lower())

    def tearDown(self):
        self.process.terminate()
        self.process.wait()
        if os.path.exists("temp"):
            shutil.rmtree("temp")

##############################################
# Main Entry Point
##############################################

if __name__ == '__main__':
    unittest.main(testRunner=unittest.TextTestRunner)