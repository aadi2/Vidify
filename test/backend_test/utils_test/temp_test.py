from backend.utils.temp import temp
import unittest
import os
import sys
import yt_dlp
import shutil
import pytest

COOKIES_FILE = "cookies.txt"


class tempTestSuite(unittest.TestCase):
    def setUp(self):
        self.video_url = "https://www.youtube.com/watch?v=cytJLvf-eVs"
        self.video_file = ""
        self.output_dir = "temp/video"
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = "temp/video/test.%(ext)s"
        ydl_opts = {
            "outtmpl": output_path,
            "format": "worst",
            "cookiefile": COOKIES_FILE,
        }

        # Download a test video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.video_url, download=True)
            info = ydl.sanitize_info(info)

            self.video_file = output_path.replace("%(ext)s", info["ext"])

        self.videoUtils = temp(self.video_file)

    # @pytest.mark.skip(reason="")
    def test_create_transcript(self):
        self.videoUtils.get_frames()

        self.assertTrue(os.path.exists("temp/frames") and os.listdir("temp/frames"), "Frames not extracted")

    def tearDown(self):
        if os.path.exists(self.video_file):
            os.remove(self.video_file)
        if os.path.exists(f"temp/frames/{os.path.splitext(os.path.basename(self.video_file))[0]}"):
            shutil.rmtree(f"temp/frames/{os.path.splitext(os.path.basename(self.video_file))[0]}")


if __name__ == "__main__":
    unittest.main(testRunner=unittest.TextTestRunner(stream=sys.stdout))
