import unittest
import sys
import subprocess
import requests
import time
import os
import shutil

BASE_URL = "http://127.0.0.1:8001"

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

        # Wait for the server to start
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
        """
        Expect 400 for non-YouTube domain (domain whitelisting).
        """
        response = requests.get(f"{BASE_URL}/?hash_id={self.invalid_domain_url}")
        self.assertEqual(response.status_code, 400)
        self.assertIn("invalid video url", response.text.lower())

    def test_malformed_url(self):
        """
        Expect 400 for a completely invalid/malformed URL.
        """
        response = requests.get(f"{BASE_URL}/?hash_id={self.malformed_url}")
        self.assertEqual(response.status_code, 400)
        self.assertIn("invalid video url", response.text.lower())

    def test_no_transcript_url(self):
        """
        If the video doesn't have an English transcript,
        expect 404 "Not able to fetch transcript."
        """
        response = requests.get(f"{BASE_URL}/?hash_id={self.no_transcript_url}")
        self.assertEqual(response.status_code, 404)
        self.assertIn("not able to fetch transcript", response.text.lower())

    def test_valid_url(self):
        """
        A valid YouTube URL that should successfully download
        video and transcript, returning 200.
        """
        response = requests.get(f"{BASE_URL}/?hash_id={self.valid_url}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("video and transcript downloaded successfully", response.text.lower())

    def test_rate_limit_exceeded(self):
        """
        Make multiple requests in quick succession to
        confirm that rate limiting returns 429 after the threshold.
        """
        final_response = None
        for _ in range(4):
            final_response = requests.get(f"{BASE_URL}/test-rate-limit")
        # The 4th request should yield 429
        self.assertEqual(final_response.status_code, 429)
        self.assertIn("too many requests", final_response.text.lower())

    def tearDown(self):
        self.process.terminate()
        self.process.wait()
        if os.path.exists("temp"):
            shutil.rmtree("temp")

if __name__ == '__main__':
    unittest.main(testRunner=unittest.TextTestRunner(stream=sys.stdout))
