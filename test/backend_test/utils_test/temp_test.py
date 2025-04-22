from backend.utils.temp import temp
import unittest
import os
import sys
import yt_dlp
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
            "format": "best[height<=480]",  # Using more flexible format selection
            "cookiefile": COOKIES_FILE,
            "ignoreerrors": True,  # Continue despite download errors
        }

        # Download a test video
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.video_url, download=True)
                if info:
                    info = ydl.sanitize_info(info)
                    self.video_file = output_path.replace("%(ext)s", info["ext"])
        except Exception as e:
            pytest.skip(f"Skipping test due to video download issue: {e}")

        self.videoUtils = temp(self.video_file)

    def test_create_transcript(self):
        # Skip if video download failed
        if not self.video_file or not os.path.exists(self.video_file):
            pytest.skip("Video file not available")

        frame_count = self.videoUtils.get_frames()

        # Get the frame paths from the temp directory structure
        frame_paths = self.videoUtils.get_frame_paths()

        # Check if frames were extracted successfully
        self.assertTrue(
            len(frame_paths) > 0, f"No frames extracted. Frame count: {frame_count}"
        )

    def tearDown(self):
        if (
            hasattr(self, "video_file")
            and self.video_file
            and os.path.exists(self.video_file)
        ):
            os.remove(self.video_file)

        # The temp directory is now managed by the temp class itself via its cleanup method
        if hasattr(self, "videoUtils"):
            self.videoUtils.cleanup()


if __name__ == "__main__":
    unittest.main(testRunner=unittest.TextTestRunner(stream=sys.stdout))
