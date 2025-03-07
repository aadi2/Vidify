from flask import Flask, jsonify, request, redirect, session
import os
import yt_dlp
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

COOKIES_FILE = "cookies.txt"

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = os.getenv('OAUTH_REDIRECT_URI', 'http://localhost:8001/oauth/callback')
SCOPE = 'https://www.googleapis.com/auth/youtube.readonly'

# Simple in-memory storage (replace with a database for production)
user_tokens = {}


def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'super-secret-key')
    
    if os.getenv('TEST_MODE') == 'true':
        @app.before_request
        def mock_auth():
            session['access_token'] = 'test-access-token'

    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "OK"}), 200

    @app.route("/login", methods=["GET"])
    def login():
        params = {
            'client_id': GOOGLE_CLIENT_ID,
            'redirect_uri': REDIRECT_URI,
            'response_type': 'code',
            'scope': SCOPE,
            'access_type': 'offline',
            'prompt': 'consent'
        }
        auth_url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode(params)
        return redirect(auth_url)

    @app.route("/oauth/callback", methods=["GET"])
    def oauth_callback():
        code = request.args.get("code")
        if not code:
            return jsonify({"error": "Authorization code not provided"}), 400

        token_url = "https://oauth2.googleapis.com/token"
        data = {
            'code': code,
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI,
            'grant_type': 'authorization_code'
        }

        response = requests.post(token_url, data=data)
        token_data = response.json()

        if 'error' in token_data:
            return jsonify({"error": token_data['error']}), 400

        session['access_token'] = token_data['access_token']
        session['refresh_token'] = token_data.get('refresh_token')  # Might be missing if user already consented
        session['token_type'] = token_data['token_type']

        return jsonify({
            "message": "Successfully authenticated",
            "access_token": session['access_token']
        })

    def validate_and_log_video_id(request_data):
        """Helper to extract and validate videoId from request JSON."""
        video_id = request_data.get("videoId")
        if not video_id:
            return None, jsonify({"error": "Missing videoId"}), 400

        print(f"Processing request for video ID: {video_id}")
        return video_id, None, None

    @app.route("/", methods=["GET"])
    def home():
        if 'access_token' not in session:
            return jsonify({"error": "Unauthorized - Please log in via /login"}), 401

        yt_url = request.args.get("hash_id")

        # TODO: Validate URL with regex for security
        if not yt_url:
            return jsonify({"error": "Missing video URL"}), 400

        filename = get_video(yt_url)
        transcript = get_transcript(yt_url)

        # TODO: Object recognition in the video (videoUtils.py)
        # TODO: Transcript search (transcriptUtils.py)

        if not filename:
            result = {"message": "Not able to download the video."}
            return jsonify(result), 404

        if not transcript:
            result = {"message": "Not able to fetch transcript."}
            return jsonify(result), 404

        print("Transcript:", transcript)
        result = {"message": "Video and transcript downloaded successfully."}
        return jsonify(result), 200

    def get_video(url):
        """
        Downloads the raw YouTube video.

        Args:
            url (str): The YouTube video URL.

        Returns:
            Optional[str]: The file name in which the video is stored if available, else None.
        """
        output_dir = "temp/video"
        os.makedirs(output_dir, exist_ok=True)
        output_path = 'temp/video/%(title)s.%(ext)s'

        ydl_opts = {
            "outtmpl": output_path,
            "format": "worst",
            "cookiefile": COOKIES_FILE,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                info = ydl.sanitize_info(info)

                filename = output_path.replace("%(title)s", info["title"]).replace("%(ext)s", info["ext"])

            if os.path.exists(filename):
                print("Download successful")
                return filename

            print("Download failed")
            return None

        except Exception as e:
            print(f"Download failed. Exception: {e}")
            return None

    def get_transcript(url, lang="en"):
        """
        Fetches the transcript for a YouTube video.

        Args:
            url (str): The YouTube video URL.
            lang (str, optional): The language code for the transcript. Defaults to "en".

        Returns:
            Optional[str]: The transcript text if available, else None.
        """
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
                subtitles = info_dict.get("subtitles") or info_dict.get("automatic_captions")

                video_title = info_dict.get("title", "unknown_video")
                transcript_url = None

                for lang_key, subs in subtitles.items():
                    if lang_key.startswith("en"):
                        for sub in subs:
                            if sub["ext"] == "vtt":
                                transcript_url = sub["url"]
                                break

            if transcript_url:
                response = requests.get(transcript_url)
                if response.status_code == 200:
                    with open(f"temp/subtitles/{video_title}.vtt", "w", encoding="utf-8") as file:
                        file.write(response.text)

                    return True

                print("Failed to fetch transcript")
                # TODO: If not available, use NLP tools
                return None

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
    app.run(port=8001, host='127.0.0.1', debug=True, use_evalex=False, use_reloader=False)
