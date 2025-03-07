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
        os.environ["TEST_MODE"] = "true"  # Enable test mode to skip auth in app.py

        self.invalid_url = "invalid_url"
        self.no_transcript_url = "https://www.youtube.com/watch?v=sD9gTAFDq40"
        self.valid_url = "https://www.youtube.com/watch?v=W86cTIoMv2U"

        self.process = subprocess.Popen([sys.executable, "src/backend/app.py"], stdout=sys.stdout, stderr=sys.stderr)

        for _ in range(6):
            try:
                response = requests.get(f"{BASE_URL}/health")
                if response.status_code == 200:
                    break
            except requests.ConnectionError:
                time.sleep(1)
        else:
            raise RuntimeError("Flask server failed to start.")

    def test_invalid_url(self):
        response = requests.get(f"{BASE_URL}/?hash_id={self.invalid_url}")
        self.assertEqual(response.status_code, 404)
        self.assertIn("not able to download the video", response.text.lower())

    def test_no_transcript_url(self):
        response = requests.get(f"{BASE_URL}/?hash_id={self.no_transcript_url}")
        self.assertEqual(response.status_code, 404)
        self.assertIn("not able to fetch transcript", response.text.lower())

    def test_valid_url(self):
        response = requests.get(f"{BASE_URL}/?hash_id={self.valid_url}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("video and transcript downloaded successfully", response.text.lower())

    def tearDown(self):
        self.process.terminate()
        self.process.wait()

        if os.path.exists("temp"):
            shutil.rmtree("temp")


if __name__ == '__main__':
    unittest.main(testRunner=unittest.TextTestRunner(stream=sys.stdout))
