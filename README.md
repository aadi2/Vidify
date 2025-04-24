# Vidify

Vidify is a Chrome Extension that revolutionizes how you interact with YouTube videos. It enables users to search for specific keywords within videos, instantly finding the exact moments they're looking for without tedious manual scrubbing.

## Features

### Transcript Search
- Search for keywords within video transcripts
- Get timestamp-linked results with highlighted matching text
- Works with YouTube's automatically generated captions

### User Experience
- Intuitive search interface with real-time results
- Progress indicators for search operations
- Visible highlighting of search terms in results
- Toggle between light and dark mode

### Technical Capabilities
- Chrome Extension with Side Panel support
- Cross-platform compatibility (Windows, macOS, Linux)
- Backend API for processing YouTube content
- Secure YouTube cookie handling for authenticated requests

### Coming Soon
- **Object Detection**: Locate when specific objects appear in videos
- Visual object detection using YOLOv8
- Support for videos with no transcripts using custom NLP models

## Architecture

Vidify consists of two main components:

### Chrome Extension (Frontend)
- **Background Service Worker**: Handles communication with the backend API
- **Content Scripts**: Integrates with YouTube for enhanced video navigation
- **Popup UI**: Clean, gradient-themed interface for video searches
- **Side Panel Support**: Enables searching without leaving the YouTube page

### Flask Server (Backend)
- **Flask API**: RESTful interface for video processing
- **YouTube Integration**: Secure downloading of video content and transcripts
- **Transcript Processing**: Natural language search capabilities
- **WebVTT Parser**: Processes and indexes caption files

## Installation

### Development Environment Setup

1. **Clone the repository**:
   ```
   git clone https://github.com/your-username/vidify.git
   cd vidify
   ```

2. **Set up the virtual environment**:

   **Windows**:
   ```
   python -m venv venv
   .\venv\Scripts\activate
   ```

   **macOS/Linux**:
   ```
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```

4. **Install pre-commit hooks**:
   ```
   pip install pre-commit
   pre-commit install
   ```

### Extension Installation

1. Navigate to Chrome://extensions
2. Switch to Developer mode
3. Click "Load Unpacked" and select the extension from `/build/extension` directory

### System Requirements
* Chrome browser (version 88 or higher)
* Internet connection for API communication
* For developers: Python 3.9+ and required dependencies

## Loading the Extension in Chrome

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" in the top-right corner
3. Click "Load unpacked" and select the `build/extension` directory
4. The Vidify extension should now appear in your browser

## Usage

1. Navigate to any YouTube video
2. Click the Vidify extension icon or open the side panel
3. Enter a keyword in the search bar
4. Click "Search" to find matching timestamps
5. Review results with highlighted matching text
6. Toggle between light and dark mode as needed
7. Use the transcript search mode for keyword searching (object detection coming soon)

## Development

### Project Structure

```
vidify/
├── .github/workflows/     # CI/CD configuration
├── docs/                  # Documentation
├── src/
│   ├── backend/           # Flask server
│   │   ├── app.py         # Main application
│   │   ├── utils/         # Utility functions
│   │   └── models/        # ML models
│   ├── extension/         # Chrome extension
│   │   ├── background/    # Background scripts
│   │   ├── content/       # Content scripts
│   │   └── manifest.json  # Extension manifest
│   └── build.py           # Build script
└── test/                  # Tests
    ├── backend_test/      # Backend tests
    └── extension_test/    # Extension tests
```

### CI/CD Infrastructure
* **GitHub Actions**: Automated testing across Windows, macOS, and Linux
* **Linting**: Code quality enforcement with Flake8 and Ruff
* **Cross-Platform Testing**: Ensures compatibility across operating systems
* **Build System**: Streamlined development and production builds

### Adding New Features

1. Create a feature branch from main
2. Implement your changes
3. Add appropriate tests
4. Ensure linting passes with `flake8` and `ruff`
5. Submit a pull request

### Testing

Run the test suite with:

```
pytest --cov=src
```

## Deployment

### Backend Deployment (Cloud Run)

The backend can be deployed to Google Cloud Run using the provided `cloudbuild.yaml` configuration.

### Extension Publishing

Once thoroughly tested, the extension can be published to the Chrome Web Store by creating a zip archive of the `build/extension` directory.


## Acknowledgements

- YOLOv9 for object detection capabilities
- yt-dlp for YouTube video downloading functionality
- Whisper for audio transcription

Must run THESE 2 COMMANDS locally:
pip install pre-commit
pre-commit install

We're so back.
