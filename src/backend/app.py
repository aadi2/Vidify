from flask import Flask, jsonify, request
import os
import yt_dlp
import requests
import re
import tempfile
import shutil
from utils.transcriptUtils import transcriptUtils
from flask_cors import CORS
import whisper
import time

COOKIES_FILE = "cookies.txt"


# Implement lazy loading for Whisper model
class WhisperModelManager:
    _instance = None
    _last_used = 0
    _timeout = 300  # 5 minutes timeout for model unloading

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            print("Loading Whisper model")
            cls._instance = whisper.load_model("tiny")
            cls._instance.to("cpu")
        cls._last_used = time.time()
        return cls._instance

    @classmethod
    def cleanup_if_idle(cls):
        if cls._instance is not None and time.time() - cls._last_used > cls._timeout:
            print("Unloading Whisper model due to inactivity")
            cls._instance = None
            # Force garbage collection to release memory
            import gc

            gc.collect()

    @classmethod
    def cleanup(cls):
        cls._instance = None


# Create a temp file manager for the entire application
class TempFileManager:
    def __init__(self):
        # Root temp directory where all temp files will be created
        self.root_temp_dir = tempfile.mkdtemp(prefix="vidify_")
        # Create subdirectories
        self.video_dir = os.path.join(self.root_temp_dir, "video")
        self.subtitle_dir = os.path.join(self.root_temp_dir, "subtitles")

        # Create directories
        os.makedirs(self.video_dir, exist_ok=True)
        os.makedirs(self.subtitle_dir, exist_ok=True)

        # Track all files for cleanup
        self.temp_files = []

    def create_temp_file(self, prefix="", suffix=""):
        temp_file = tempfile.NamedTemporaryFile(
            dir=self.root_temp_dir, prefix=prefix, suffix=suffix, delete=False
        )
        self.temp_files.append(temp_file.name)
        return temp_file.name

    def create_video_path(self, name, ext):
        path = os.path.join(self.video_dir, f"{name}.{ext}")
        return path

    def create_subtitle_path(self, name):
        path = os.path.join(self.subtitle_dir, f"{name}.vtt")
        return path

    def cleanup_file(self, file_path):
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                self.temp_files.remove(
                    file_path
                ) if file_path in self.temp_files else None
            except Exception as e:
                print(f"Error removing file {file_path}: {e}")

    def cleanup(self):
        # Clean up individual files
        for file in self.temp_files:
            if os.path.exists(file):
                try:
                    os.remove(file)
                except Exception as e:
                    print(f"Error removing file {file}: {e}")

        # Clean up root directory including all subdirectories
        if os.path.exists(self.root_temp_dir):
            try:
                shutil.rmtree(self.root_temp_dir)
            except Exception as e:
                print(f"Error removing temp directory {self.root_temp_dir}: {e}")


# Regular expression for validating YouTube URLs
YOUTUBE_URL_PATTERN = (
    r"^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[a-zA-Z0-9_-]{11}(&.*)?$"
)


def is_valid_youtube_url(url):
    """
    Validates if the provided URL is a valid YouTube video URL.

    Args:
        url (str): The URL to validate

    Returns:
        bool: True if the URL is a valid YouTube URL, False otherwise
    """
    if not url:
        return False
    return bool(re.match(YOUTUBE_URL_PATTERN, url))


def create_app():
    app = Flask(__name__)
    CORS(app)

    # Create the temp file manager
    temp_manager = TempFileManager()

    # Create HTTP session for reuse
    http_session = requests.Session()

    # Store as app config
    app.config["TEMP_MANAGER"] = temp_manager
    app.config["HTTP_SESSION"] = http_session

    @app.route("/", methods=["GET"])
    def home():
        # Clean up whisper model if idle
        WhisperModelManager.cleanup_if_idle()
        return Flask.redirect("/object_search")

    @app.route("/object_search", methods=["GET"])
    def object_search():
        try:
            yt_url = request.args.get("yt_url")

            # Validate the YouTube URL
            if not is_valid_youtube_url(yt_url):
                return jsonify(
                    {
                        "message": "Invalid YouTube URL. Please provide a valid YouTube video URL.",
                        "results": None,
                    }
                ), 400

            # keyword = request.args.get("keyword")
            # TODO: authentication
            filename = get_video(yt_url, temp_manager)
            # Needed later for optimization:
            # transcript = get_transcript(yt_url)
            # TODO: Object recogniton in the video (videoUtils.py)

            if not filename:
                result = {"message": "Not able to download the video.", "results": None}

                return jsonify(result), 404
            else:
                # Temporary:
                response = {
                    "message": "Object search is not implemented yet.",
                    "results": [],
                }
                print(response)

                # Clean up temp files
                temp_manager.cleanup_file(filename)

                return jsonify(response), 404
        except Exception as e:
            print(f"An exception occurred: {e}")
            return jsonify({"message": "Internal server error", "error": str(e)}), 500

    @app.route("/transcript_search", methods=["GET"])
    def transcript_search():
        try:
            yt_url = request.args.get("yt_url")

            # Validate the YouTube URL
            if not is_valid_youtube_url(yt_url):
                return jsonify(
                    {
                        "message": "Invalid YouTube URL. Please provide a valid YouTube video URL.",
                        "results": None,
                    }
                ), 400

            keyword = request.args.get("keyword")
            transcript = get_transcript(yt_url, http_session, temp_manager)

            if not transcript:
                # Get the whisper model instance
                model = WhisperModelManager.get_instance()

                transcript_utils = transcriptUtils()
                file = transcript_utils.create_transcript(yt_url, transcript, model)

                if not file:
                    result = {
                        "message": "Not able to fetch transcript.",
                        "results": None,
                    }
                    print(result)

                    return jsonify(result), 404
                else:
                    file = os.path.basename(file)
                    results = transcript_utils.search_transcript(file, keyword)
                    formatted_results = [
                        {"timestamp": r[0], "text": r[1]} for r in results
                    ]
                    response = {
                        "message": "Transcript downloaded successfully.",
                        "results": formatted_results,
                    }
                    print(response)

                    # Clean up
                    transcript_utils.cleanup()

                    return jsonify(response), 200
            else:
                transcript_utils = transcriptUtils()
                try:
                    results = transcript_utils.search_transcript(transcript, keyword)
                    formatted_results = [
                        {"timestamp": r[0], "text": r[1]} for r in results
                    ]
                    response = {
                        "message": "Transcript downloaded successfully.",
                        "results": formatted_results,
                    }
                    print(response)

                    return jsonify(response), 200
                finally:
                    # Ensure cleanup happens
                    transcript_utils.cleanup()
                    temp_manager.cleanup_file(
                        os.path.join(temp_manager.subtitle_dir, transcript)
                    )

        except yt_dlp.utils.DownloadError as e:
            print(f"Download error: {e}")
            return jsonify(
                {"message": "Not able to fetch transcript.", "error": str(e)}
            ), 404
        except Exception as e:
            print(f"An exception occurred: {e}")
            return jsonify({"message": "Internal error", "error": str(e)}), 500

    @app.route("/health", methods=["GET"])
    def health_check():
        # Clean up whisper model if idle
        WhisperModelManager.cleanup_if_idle()
        return jsonify({"status": "OK"}), 200

    """Downloads the raw YouTube video.

    Args:
        url (str): The YouTube video URL.

    Returns:
        Optional[str]: The file name in which the video is stored if available, else None.
    """

    def get_video(url, temp_manager):
        try:
            # Use a context manager for the temporary directory
            output_path = os.path.join(temp_manager.video_dir, "%(title)s.%(ext)s")

            ydl_opts = {
                "outtmpl": output_path,
                "format": "worst",
                "cookiefile": COOKIES_FILE,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                info = ydl.sanitize_info(info)

                filename = output_path.replace("%(title)s", info["title"]).replace(
                    "%(ext)s", info["ext"]
                )

            if os.path.exists(filename):
                print("Download successful")
                # Add file to temp files for tracking
                temp_manager.temp_files.append(filename)
                return filename
            else:
                print("Download failed")
                return None
        except Exception as e:
            print(f"Download failed. Exception: {e}")
            return None

    """Fetches the transcript for a YouTube video.

    Args:
        url (str): The YouTube video URL.
        lang (str, optional): The language code for the transcript. Defaults to "en".

    Returns:
        Optional[str]: The transcript text if available, else None.
    """

    def get_transcript(url, http_session, temp_manager, lang="en"):
        try:
            ydl_opts = {
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitleslangs": [lang],
                "skip_download": True,
                "cookiefile": COOKIES_FILE,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                subtitles = info_dict.get("subtitles") or info_dict.get(
                    "automatic_captions"
                )

                video_title = info_dict.get("title", "unknown_video")
                transcript_url = None

                for lang, subs in subtitles.items():
                    if lang.startswith("en"):
                        for sub in subs:
                            if sub["ext"] == "vtt":
                                transcript_url = sub["url"]
                                break

            if transcript_url:
                # Use session for HTTP requests to reuse connections
                response = http_session.get(transcript_url)
                if response.status_code == 200:
                    # Use temp manager for file path
                    subtitle_path = temp_manager.create_subtitle_path(video_title)

                    with open(subtitle_path, "w", encoding="utf-8") as file:
                        file.write(response.text)

                    # Add to tracked files
                    temp_manager.temp_files.append(subtitle_path)
                    return f"{video_title}.vtt"
                else:
                    print("Failed to fetch transcript")
                    return None
            else:
                print("Failed to fetch transcript")
                return None
        except Exception as e:
            print(f"An error occurred when fetching the transcript. Exception {e}")
            return None

    # Register cleanup on application teardown
    @app.teardown_appcontext
    def cleanup_resources(error):
        WhisperModelManager.cleanup()
        if "TEMP_MANAGER" in app.config:
            app.config["TEMP_MANAGER"].cleanup()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(
        port=8001, host="127.0.0.1", debug=True, use_evalex=False, use_reloader=False
    )
    # app.run(port=8080, host='0.0.0.0', debug=True,
    #         use_evalex=False, use_reloader=False)
