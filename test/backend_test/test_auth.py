import unittest
import sys
import subprocess
import requests
import time
import os
import shutil

BASE_URL = "http://127.0.0.1:8001"


class AuthTestSuite(unittest.TestCase):
    def setUp(self):
        if "TEST_MODE" in os.environ:
            del os.environ["TEST_MODE"]  # Ensure TEST_MODE is off for this test

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

    def test_requires_auth(self):
        response = requests.get(f"{BASE_URL}/?hash_id=invalid_url")
        self.assertEqual(response.status_code, 401)
        self.assertIn("unauthorized", response.text.lower())

    def tearDown(self):
        self.process.terminate()
        self.process.wait()

        if os.path.exists("temp"):
            shutil.rmtree("temp")


if __name__ == '__main__':
    unittest.main(testRunner=unittest.TextTestRunner(stream=sys.stdout))
