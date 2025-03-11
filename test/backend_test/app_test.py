import unittest
import sys
import subprocess
import requests
import time
import os
import pytest
import shutil

BASE_URL = "http://127.0.0.1:8001"

class TestSuite(unittest.TestCase):
    def setUp(self):
        self.invalid_url = "invalid_url"
        self.no_transcript_url = "https://www.youtube.com/watch?v=sD9gTAFDq40"
        self.valid_url = "https://www.youtube.com/watch?v=W86cTIoMv2U"
        self.keyword = "cat"

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
        
    # @pytest.mark.skip(reason="Have to fix cookies first. Avoiding blocking the development.")
    def test_app(self):
        with self.subTest(key=self.invalid_url):
            response = requests.get(f"{BASE_URL}/?yt_url={self.invalid_url}&keyword={self.keyword}")
            print(response)
            self.assertEqual(response.status_code, 404)
            self.assertIn("not able to download the video", response.text.lower())

        with self.subTest(key=self.no_transcript_url):
            response = requests.get(f"{BASE_URL}/?yt_url={self.no_transcript_url}&keyword={self.keyword}")
            self.assertEqual(response.status_code, 404)
            self.assertIn("not able to fetch transcript", response.text.lower())

        with self.subTest(key=self.valid_url):
            response = requests.get(f"{BASE_URL}/?yt_url={self.valid_url}&keyword={self.keyword}")
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

if __name__ == '__main__':
    unittest.main(testRunner=unittest.TextTestRunner(stream=sys.stdout))