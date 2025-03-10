from flask import Flask, jsonify, request, redirect, session
from flask_cors import CORS
import os
import yt_dlp
import requests
from urllib.parse import urlencode, urlparse, urlunparse, quote
from dotenv import load_dotenv
import re

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

import whisper
model = whisper.load_model("small")

COOKIES_FILE = "cookies.txt"

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = os.getenv('OAUTH_REDIRECT_URI', 'http://localhost:5000/oauth/callback')
SCOPE = 'https://www.googleapis.com/auth/youtube.readonly'

# Simple in-memory storage (replace with a database for production)
user_tokens = {}


def is_valid_youtube_url(url):
    """
    Validate the YouTube URL using regex and domain whitelisting.
    Accepts URLs from youtube.com/watch?v=... and youtu.be/...
    """
    pattern = re.compile(r"^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]+")
    return bool(pattern.match(url))


def sanitize_url(url):
    """
    Sanitize the URL by parsing and safely quoting its components.
    """
    parsed = urlparse(url)
    safe_path = quote(parsed.path)
    safe_query = quote(parsed.query, safe="=&")
    return urlunparse((parsed.scheme, parsed.netloc, safe_path, parsed.params, safe_query, parsed.fragment))


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'super-secret-key')

    # Set up rate limiting: 10 requests per minute by default
    limiter = Limiter(key_func=get_remote_address, default_limits=["10 per minute"])
    limiter.init_app(app)

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

    @app.route("/verify-token", methods=["POST"])
    def verify_token():
        """
        Verifies the access token sent from the Chrome extension by querying Google’s UserInfo API.
        """
        data = request.json
        access_token = data.get("accessToken")
        if not access_token:
            return jsonify({"error": "Missing access token"}), 400

        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get("https://www.googleapis.com/oauth2/v2/userinfo", headers=headers)
        if response.status_code == 200:
            user_info = response.json()
            return jsonify({"message": "Token valid", "user": user_info}), 200
        else:
            return jsonify({"error": "Invalid token"}), 401

    # Home route for video & transcript download (existing functionality)
    @app.route("/", methods=["GET"])
    @limiter.limit("10 per minute")
    def home():
        if 'access_token' not in session:
            return jsonify({"error": "Unauthorized - Please log in via /login"}), 401

        yt_url = request.args.get("hash_id")

        # TODO: Validate URL with regex for security
        if not yt_url:
            return jsonify({"error": "Missing video URL"}), 400

        if not is_valid_youtube_url(yt_url):
            app.logger.warning(f"Invalid YouTube URL attempted: {yt_url}")
            return jsonify({"error": "Invalid video URL"}), 400

        safe_url = sanitize_url(yt_url)
        filename = get_video(safe_url)
        transcript = get_transcript(safe_url)

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

    # Route for transcript search integrating transcriptUtils.py
    @app.route("/search/transcript", methods=["POST"])
    def search_transcript():
        data = request.json or {}
        video_id = data.get("videoId")
        yt_url = data.get("ytUrl")       # Expect full YouTube URL
        search_term = data.get("searchTerm")

        if not yt_url or not video_id or not search_term:
            return jsonify({"error": "Missing one of ytUrl, videoId, or searchTerm"}), 400

        # Import transcriptUtils (adjust the import if needed)
        from backend.utils.transcriptUtils import transcriptUtils
        t_utils = transcriptUtils()
        vtt_filename = f"{video_id}.vtt"
        vtt_path = os.path.join("temp/subtitles", vtt_filename)

        # Create the transcript if it doesn't exist
        if not os.path.exists(vtt_path):
            created_file = t_utils.create_transcript(yt_url, video_id, model)
            if not created_file:
                return jsonify({"error": "Failed to create transcript"}), 500
            # Rename if the created file doesn't match our expected path
            if created_file != vtt_path:
                os.rename(created_file, vtt_path)

        # Attempt to search the transcript; catch exceptions to prevent "Unknown error"
        try:
            matches = t_utils.search_transcript(vtt_filename, search_term)
        except Exception as e:
            return jsonify({"error": f"Transcript search error: {str(e)}"}), 500

        results = [{"timestamp": ts, "text": text} for ts, text in matches]
        return jsonify({"results": results}), 200
    
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

    @app.route("/test-rate-limit", methods=["GET"])
    @limiter.limit("3 per minute")
    def test_rate_limit():
        return jsonify({"message": "This is a rate-limited endpoint."}), 200

    return app


if __name__ == "__main__":
    if not os.path.exists("temp"):
        os.makedirs("temp")

    app = create_app()
    app.run(port=5000, host='127.0.0.1', debug=True,
            use_evalex=False, use_reloader=False)
    # app.run(port=8080, host='0.0.0.0', debug=True,
    #         use_evalex=False, use_reloader=False)
