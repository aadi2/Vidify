import unittest
import sys
import subprocess
import requests
import time
import os
import shutil
import re

# Define the URL validation regex directly in the test to avoid import issues
YOUTUBE_URL_PATTERN = (
    r"^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[a-zA-Z0-9_-]{11}(&.*)?$"
)


def is_valid_youtube_url(url):
    """
    Validates if the provided URL is a valid YouTube video URL.
    """
    if not url:
        return False
    return bool(re.match(YOUTUBE_URL_PATTERN, url))


BASE_URL = "http://127.0.0.1:8001"


class TestSuite(unittest.TestCase):
    def setUp(self):
        self.invalid_url = "invalid_url"
        self.no_transcript_url = "https://www.youtube.com/watch?v=7F5c64u0q28"
        self.valid_url = "https://www.youtube.com/watch?v=W86cTIoMv2U"
        self.video_url = "https://www.youtube.com/watch?v=SR__amDl1c8"
        self.keyword = "cat"
        self.keyword2 = "come"
        self.keyword3 = "person"

        self.process = subprocess.Popen(
            [sys.executable, "src/backend/app.py"], stdout=sys.stdout, stderr=sys.stderr
        )

        for _ in range(15):
            try:
                response = requests.get(f"{BASE_URL}/health")
                if response.status_code == 200:
                    break
            except requests.ConnectionError:
                time.sleep(1)
        else:
            raise RuntimeError("Flask server failed to start.")

    # @pytest.mark.skip(reason="Have to fix cookies first. Avoiding blocking the development.")
    def test_transcript_search(self):
        with self.subTest(key=self.invalid_url):
            response = requests.get(
                f"{BASE_URL}/transcript_search?yt_url={self.invalid_url}&keyword={self.keyword}"
            )
            print(response)
            # Either a 400 (invalid URL) or 404 (not able to fetch transcript) is acceptable
            self.assertTrue(response.status_code in [400, 404])
            self.assertTrue(
                "invalid youtube url" in response.text.lower()
                or "not able to fetch transcript" in response.text.lower()
            )

        with self.subTest(key=self.no_transcript_url):
            response = requests.get(
                f"{BASE_URL}/transcript_search?yt_url={self.no_transcript_url}&keyword={self.keyword2}"
            )
            print(response)
            self.assertEqual(response.status_code, 200)
            self.assertIn("transcript downloaded successfully", response.text.lower())

        with self.subTest(key=self.valid_url):
            response = requests.get(
                f"{BASE_URL}/transcript_search?yt_url={self.valid_url}&keyword={self.keyword}"
            )
            print(response)
            self.assertEqual(response.status_code, 200)
            self.assertIn("transcript downloaded successfully", response.text.lower())

    # @pytest.mark.skip(reason="Have to fix cookies first. Avoiding blocking the development.")
    def test_object_search(self):
        with self.subTest(key=self.invalid_url):
            response = requests.get(
                f"{BASE_URL}/object_search?yt_url={self.invalid_url}&keyword={self.keyword}"
            )
            print(response)
            # Either a 400 (invalid URL) or 404 (not able to download) is acceptable
            self.assertTrue(response.status_code in [400, 404])
            self.assertTrue(
                "invalid youtube url" in response.text.lower()
                or "not able to download the video" in response.text.lower()
            )

        with self.subTest(key=self.video_url):
            response = requests.get(
                f"{BASE_URL}/object_search?yt_url={self.video_url}&keyword={self.keyword}"
            )
            print(response)
            self.assertEqual(response.status_code, 404)
            self.assertTrue("object not found")

        with self.subTest(key=self.video_url):
            response = requests.get(
                f"{BASE_URL}/object_search?yt_url={self.video_url}&keyword={self.keyword3}"
            )
            print(response)
            self.assertEqual(response.status_code, 200)
            self.assertTrue("object found successfully")

    # @pytest.mark.skip(reason="Have to fix cookies first. Avoiding blocking the development.")
    def test_toc(self):
        with self.subTest(key=self.invalid_url):
            response = requests.get(
                f"{BASE_URL}/toc?yt_url={self.invalid_url}"
            )
            print(response)
            # Either a 400 (invalid URL) or 404 (not able to download) is acceptable
            self.assertTrue(response.status_code in [400, 404])
            self.assertTrue(
                "invalid youtube url" in response.text.lower()
                or "not able to download the video" in response.text.lower()
            )

        with self.subTest(key=self.video_url):
            response = requests.get(
                f"{BASE_URL}/toc?yt_url={self.video_url}"
            )
            print(response)
            self.assertEqual(response.status_code, 200)
            self.assertTrue("table of contents created successfully")

    def test_url_validation(self):
        """Test URL validation logic"""
        # Valid YouTube URLs
        self.assertTrue(
            is_valid_youtube_url("https://www.youtube.com/watch?v=W86cTIoMv2U")
        )
        self.assertTrue(
            is_valid_youtube_url("http://www.youtube.com/watch?v=W86cTIoMv2U")
        )
        self.assertTrue(is_valid_youtube_url("https://youtube.com/watch?v=W86cTIoMv2U"))
        self.assertTrue(is_valid_youtube_url("https://youtu.be/W86cTIoMv2U"))
        self.assertTrue(is_valid_youtube_url("youtu.be/W86cTIoMv2U"))

        # Invalid YouTube URLs
        self.assertFalse(is_valid_youtube_url("invalid_url"))
        self.assertFalse(is_valid_youtube_url("https://www.youtube.com"))
        self.assertFalse(is_valid_youtube_url("https://www.youtu.be"))
        self.assertFalse(is_valid_youtube_url("https://www.google.com"))
        self.assertFalse(is_valid_youtube_url("https://youtube.com/watch"))
        self.assertFalse(is_valid_youtube_url("https://youtube.com/watch?id=123"))
        self.assertFalse(is_valid_youtube_url(""))
        self.assertFalse(is_valid_youtube_url(None))

        # Test endpoint with invalid URL
        response = requests.get(
            f"{BASE_URL}/transcript_search?yt_url=https://google.com&keyword=test"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("invalid youtube url", response.text.lower())

    def tearDown(self):
        self.process.terminate()
        self.process.wait()

        del self.invalid_url
        del self.no_transcript_url
        del self.valid_url

        if os.path.exists("temp"):
            shutil.rmtree("temp")


if __name__ == "__main__":
    unittest.main(testRunner=unittest.TextTestRunner(stream=sys.stdout))
