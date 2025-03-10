import subprocess
import sys
import os
import shutil
import time


def backend():
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    )
    p = subprocess.Popen([sys.executable, "src/backend/app.py"])
    time.sleep(10)
    p.terminate()
    p.wait()


def frontend():
    frontend = "src/extension/"
    output = "../build/extension/"

    if os.path.exists(output):
        shutil.rmtree(output)

    shutil.copytree(frontend, output)


if __name__ == "__main__":
    # build backend (Remote API and video processing)
    backend()
    # build frontend (Chrome Extension)
    frontend()
