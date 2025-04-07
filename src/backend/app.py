from flask import Flask, jsonify, request
import os
import yt_dlp
import requests
from utils.transcriptUtils import transcriptUtils
from flask_cors import CORS

COOKIES_FILE = "cookies.txt"


def create_app():
    app = Flask(__name__)
    CORS(app)

    @app.route("/", methods=["GET"])
    def home():
        yt_url = request.args.get("yt_url")
        keyword = request.args.get("keyword")
        # TODO: validate url with regex for security
        # TODO: authentication
        filename = get_video(yt_url)
        transcript = get_transcript(yt_url)
        # TODO: Object recogniton in the video (videoUtils.py)
        # TODO: Transcript search (transcriptUtils.py)

        if not filename:
            result = {"message": "Not able to download the video.", "results": None}

            return jsonify(result), 404
        elif not transcript:
            result = {"message": "Not able to fetch transcript.", "results": None}

            os.remove(filename)

            return jsonify(result), 404
        else:
            # print("Transcript: ", transcript)
            transcript_utils = transcriptUtils()
            results = transcript_utils.search_transcript(transcript, keyword)
            formatted_results = [{"timestamp": r[0], "text": r[1]} for r in results]
            response = {
                "message": "Video and transcript downloaded successfully.",
                "results": formatted_results,
            }
            print(response)

            os.remove(filename)
            os.remove("temp/subtitles/" + transcript)

            return jsonify(response), 200

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
            print(f"Failed to fetch transcript. Exception {e}")
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
