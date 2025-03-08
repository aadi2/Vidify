from flask import Flask, jsonify, request, redirect, session
import os
import yt_dlp
import requests
from urllib.parse import urlencode, urlparse, urlunparse, quote
from dotenv import load_dotenv
import re
import logging

# Import rate limiting
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

COOKIES_FILE = "cookies.txt"

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = os.getenv('OAUTH_REDIRECT_URI', 'http://localhost:8001/oauth/callback')
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
    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'super-secret-key')
    
    # Initialize limiter without passing app directly.
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
        session['refresh_token'] = token_data.get('refresh_token')
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

    def validate_and_log_video_id(request_data):
        """Helper to extract and validate videoId from request JSON."""
        video_id = request_data.get("videoId")
        if not video_id:
            return None, jsonify({"error": "Missing videoId"}), 400
        app.logger.info(f"Processing request for video ID: {video_id}")
        return video_id, None, None

    @app.route("/", methods=["GET"])
    @limiter.limit("10 per minute")
    def home():
        if 'access_token' not in session:
            return jsonify({"error": "Unauthorized - Please log in via /login"}), 401

        yt_url = request.args.get("hash_id")
        if not yt_url:
            return jsonify({"error": "Missing video URL"}), 400

        # Validate and sanitize the YouTube URL
        if not is_valid_youtube_url(yt_url):
            app.logger.warning(f"Invalid YouTube URL attempted: {yt_url}")
            return jsonify({"error": "Invalid video URL"}), 400

        safe_url = sanitize_url(yt_url)
        filename = get_video(safe_url)
        transcript = get_transcript(safe_url)

        if not filename:
            return jsonify({"message": "Not able to download the video."}), 404

        if not transcript:
            return jsonify({"message": "Not able to fetch transcript."}), 404

        app.logger.info("Transcript successfully retrieved.")
        return jsonify({"message": "Video and transcript downloaded successfully."}), 200

    def get_video(url):
        """
        Downloads the raw YouTube video.
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
                app.logger.info("Download successful")
                return filename
            app.logger.error("Download failed")
            return None
        except Exception as e:
            app.logger.error(f"Download failed. Exception: {e}")
            return None

    def get_transcript(url, lang="en"):
        """
        Fetches the transcript for a YouTube video.
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
                app.logger.error("Failed to fetch transcript: Bad response status")
                return None
            app.logger.error("Failed to fetch transcript: No transcript URL found")
            return None
        except Exception as e:
            app.logger.error(f"Failed to fetch transcript. Exception {e}")
            return None

    return app

if __name__ == "__main__":
    if not os.path.exists("temp"):
        os.makedirs("temp")
    app = create_app()
    app.run(port=8001, host='127.0.0.1', debug=True, use_evalex=False, use_reloader=False)
