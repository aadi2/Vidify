import sys
import os

# Add src to PYTHONPATH dynamically
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import pytest
import subprocess
from unittest.mock import patch
from build import backend  # Correct import now accessible due to sys.path.insert()

@patch('subprocess.check_call')
@patch('subprocess.Popen')
def test_backend(mock_popen, mock_check_call):
    # Simulate backend() running successfully
    backend()

    # Assert that dependencies were installed correctly
    mock_check_call.assert_called_once_with([
        sys.executable, "-m", "pip", "install", "-r", "src/backend/requirements.txt"
    ])

    # Assert that the backend app was started
    mock_popen.assert_called_once_with([sys.executable, "src/backend/app.py"])
