from flask import Flask, jsonify, request
import os
import yt_dlp
import requests
import re
from utils.transcriptUtils import transcriptUtils
from flask_cors import CORS
import whisper

COOKIES_FILE = "cookies.txt"

print("Loading Whisper model")
WHISPER_MODEL = whisper.load_model("tiny")
WHISPER_MODEL.to("cpu")

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

    app.config["WHISPER_MODEL"] = WHISPER_MODEL

    @app.route("/", methods=["GET"])
    def home():
        Flask.redirect("/object_search")

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
            filename = get_video(yt_url)
            # Needed later for optimization:
            # transcript = get_transcript(yt_url)
            # TODO: Object recogniton in the video (videoUtils.py)

            if not filename:
                result = {"message": "Not able to download the video.", "results": None}

                return jsonify(result), 404
                # Needed later for optimization:
                """
                elif not transcript:
                    result = {"message": "Not able to fetch transcript.", "results": None}

                    os.remove(filename)

                    return jsonify(result), 404
                """
            else:
                # Needed later for optimization:
                """
                transcript_utils = transcriptUtils()
                results = transcript_utils.search_transcript(transcript, keyword)
                formatted_results = [{"timestamp": r[0], "text": r[1]} for r in results]
                response = {
                    "message": "Video and transcript downloaded successfully.",
                    "results": formatted_results,
                }
                """
                # Temporary:
                response = {
                    "message": "Object search is not implemented yet.",
                    "results": [],
                }
                print(response)

                os.remove(filename)
                # Needed later for optimization:
                # os.remove("temp/subtitles/" + transcript)

                return jsonify(response), 404
        except Exception as e:
            print("An exception occured.")
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
            transcript = get_transcript(yt_url)

            if not transcript:
                model = app.config["WHISPER_MODEL"]
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

                    os.remove("temp/subtitles/" + file)

                    return jsonify(response), 200
            else:
                transcript_utils = transcriptUtils()
                results = transcript_utils.search_transcript(transcript, keyword)
                formatted_results = [{"timestamp": r[0], "text": r[1]} for r in results]
                response = {
                    "message": "Transcript downloaded successfully.",
                    "results": formatted_results,
                }
                print(response)

                os.remove("temp/subtitles/" + transcript)

                return jsonify(response), 200
        except yt_dlp.utils.DownloadError as e:
            print("An exception occured.")
            print(e)
            return jsonify(
                {"message": "Not able to fetch transcript.", "error": str(e)}
            ), 404
        except Exception as e:
            print("An exception occured.")
            print(e)
            return jsonify({"message": "Internal  error", "error": str(e)}), 500

    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "OK"}), 200

    """Downloads the raw YouTube video.

    Args:
        url (str): The YouTube video URL.

    Returns:
        Optional[str]: The file name in which the video is stored if available, else None.
    """

    def get_video(url):
        output_dir = "temp/video"
        os.makedirs(output_dir, exist_ok=True)
        output_path = "temp/video/%(title)s.%(ext)s"
        ydl_opts = {
            "outtmpl": output_path,
            "format": "worst",
            "cookiefile": COOKIES_FILE,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                info = ydl.sanitize_info(info)

                filename = output_path.replace("%(title)s", info["title"]).replace(
                    "%(ext)s", info["ext"]
                )

            if os.path.exists(filename):
                print("Download successful")
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

    def get_transcript(url, lang="en"):
        os.makedirs("temp/subtitles", exist_ok=True)

        ydl_opts = {
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": [lang],
            "skip_download": True,
            "cookiefile": COOKIES_FILE,
        }

        try:
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
                                # TODO: make sure that vtt is the optimal format
                                break

            if transcript_url:
                response = requests.get(transcript_url)
                if response.status_code == 200:
                    with open(
                        f"temp/subtitles/{video_title}.vtt", "w", encoding="utf-8"
                    ) as file:
                        file.write(response.text)

                    return f"{video_title}.vtt"
                else:
                    print("Failed to fetch transcript")
                    # TODO: If not available, use NLP tools
                    return None
            else:
                print("Failed to fetch transcript")
                # TODO: If not available, use NLP tools
                return None
        except Exception as e:
            print(f"An error occured when fetching the transcript. Exception {e}")
            return None

    return app


if __name__ == "__main__":
    if not os.path.exists("temp"):
        os.makedirs("temp")
    app = create_app()
    app.run(
        port=8001, host="127.0.0.1", debug=True, use_evalex=False, use_reloader=False
    )
    # app.run(port=8080, host='0.0.0.0', debug=True,
    #         use_evalex=False, use_reloader=False)
