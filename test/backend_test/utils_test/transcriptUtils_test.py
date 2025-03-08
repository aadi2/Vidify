from backend.utils.transcriptUtils import transcriptUtils
import whisper
import unittest
import os
import sys

class TranscriptUtilsTestSuite(unittest.TestCase):
    def setUp(self):
        self.no_transcript_url = "https://www.youtube.com/watch?v=sD9gTAFDq40"
        self.file_path = ""

    def test_create_transcript(self):
        t_utils = transcriptUtils()
        model = whisper.load_model("tiny") # testing with smaller model for faster test run
        self.file_path = t_utils.create_transcript(self.no_transcript_url, "test_transcript", model)

        self.assertTrue(self.file_path)
        self.assertTrue(os.path.exists("temp/subtitles/test_transcript.vtt"), "Transcript not created.")

    def tearDown(self):
        if os.path.exists(self.file_path):
            os.remove(self.file_path)

if __name__ == '__main__':
    unittest.main(testRunner=unittest.TextTestRunner(stream=sys.stdout))
