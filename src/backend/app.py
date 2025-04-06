from flask import Flask, jsonify, request, redirect, session, url_for
import os
import yt_dlp
import requests
import datetime
import logging
import json
import secrets
import re
from functools import wraps
from utils.transcriptUtils import transcriptUtils
from utils.url_validator import is_valid_youtube_url, extract_video_id
from flask_cors import CORS
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
from authlib.common.security import generate_token

# Load environment variables
load_dotenv()

COOKIES_FILE = "cookies.txt"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("auth.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("auth")


def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Set up secure session with a random secret key
    app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(24))
    
    # Session configuration
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )
    
    # OAuth configuration
    app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
    app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')
    app.config['OAUTH_REDIRECT_URI'] = os.getenv('OAUTH_REDIRECT_URI')
    app.config['VALID_EXTENSION_ID'] = os.getenv('VALID_EXTENSION_ID', 'your_chrome_extension_id')
    
    # Setup OAuth
    oauth = OAuth(app)
    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )
    
    # User auth state storage - in production, use a real database
    user_tokens = {}
    
    def auth_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            
            # Check if token is in the headers
            if 'Authorization' in request.headers:
                auth_header = request.headers['Authorization']
                if auth_header.startswith('Bearer '):
                    token = auth_header.split('Bearer ')[1]
            
            if not token:
                logger.warning(f"Access attempt without token: {request.remote_addr}")
                return jsonify({'message': 'Authentication required'}), 401
            
            # Check if token is valid in our storage
            user_id = None
            for uid, user_data in user_tokens.items():
                if user_data.get('access_token') == token:
                    user_id = uid
                    break
            
            if not user_id:
                logger.warning(f"Invalid token used: {request.remote_addr}")
                return jsonify({'message': 'Invalid or expired token'}), 401
            
            # Check if token is expired
            token_data = user_tokens[user_id]
            if datetime.datetime.utcnow() > token_data.get('expires_at', datetime.datetime.min):
                logger.warning(f"Expired token used: {request.remote_addr}")
                return jsonify({'message': 'Token has expired'}), 401
            
            return f(user_id, *args, **kwargs)
        return decorated
    
    def validate_extension_request():
        # Check if the request includes Chrome extension ID in headers
        extension_id = request.headers.get('X-Extension-Id')
        valid_extension_id = app.config['VALID_EXTENSION_ID']
        
        if not extension_id or extension_id != valid_extension_id:
            logger.warning(f"Invalid extension ID: {extension_id} from {request.remote_addr}")
            return False
        return True

    @app.route('/auth/login')
    def login():
        """
        Initiate the Google OAuth login flow.
        """
        if not validate_extension_request():
            logger.warning(f"Unauthorized login attempt from {request.remote_addr}")
            return jsonify({"message": "Unauthorized request"}), 403
            
        # Generate a state parameter to prevent CSRF
        state = generate_token(32)
        session['oauth_state'] = state
        
        redirect_uri = url_for('auth_callback', _external=True)
        return oauth.google.authorize_redirect(redirect_uri, state=state)
    
    @app.route('/auth/callback')
    def auth_callback():
        """
        Callback endpoint for OAuth2 authorization.
        """
        try:
            # Verify the state parameter
            if 'oauth_state' not in session or request.args.get('state') != session['oauth_state']:
                logger.warning(f"Invalid OAuth state from {request.remote_addr}")
                return jsonify({"message": "Invalid state parameter"}), 403
            
            # Get the authorization token
            token = oauth.google.authorize_access_token()
            if not token:
                logger.error(f"Failed to get access token from {request.remote_addr}")
                return jsonify({"message": "Authentication failed"}), 401
                
            # Get user info from Google
            user_info = oauth.google.parse_id_token(token)
            user_id = user_info.get('sub')  # Google's unique user ID
            
            if not user_id:
                logger.error(f"Failed to get user ID from token")
                return jsonify({"message": "Authentication failed"}), 401
                
            # Generate our own access token for the extension
            access_token = generate_token(32)  # Generate a random token
            expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            
            # Store the token with user information (in production, use a database)
            user_tokens[user_id] = {
                'access_token': access_token,
                'user_info': user_info,
                'expires_at': expires_at
            }
            
            # Create a response page that will send the token back to the extension
            logger.info(f"Authentication successful for user: {user_info.get('email')}")
            
            # Return a page that will post the token back to the extension
            return f"""
            <html>
            <head>
                <title>Authentication Successful</title>
                <script>
                    window.onload = function() {{
                        // Post the token back to the extension
                        window.opener.postMessage({{
                            type: 'vidify_auth_token',
                            token: '{access_token}',
                            expires_at: '{expires_at.isoformat()}'
                        }}, '*');
                        // Close this window
                        window.close();
                    }};
                </script>
            </head>
            <body>
                <h1>Authentication Successful!</h1>
                <p>You can close this window and return to the extension.</p>
            </body>
            </html>
            """
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return jsonify({"message": "Authentication failed"}), 500
    
    @app.route("/auth/validate", methods=["GET"])
    def validate_token():
        """
        Validate if a token is still valid
        """
        token = None
        
        # Check if token is in the headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split('Bearer ')[1]
        
        if not token:
            return jsonify({'valid': False, 'message': 'No token provided'}), 401
        
        # Check if token exists in our storage
        user_id = None
        for uid, user_data in user_tokens.items():
            if user_data.get('access_token') == token:
                user_id = uid
                break
        
        if not user_id:
            return jsonify({'valid': False, 'message': 'Invalid token'}), 401
        
        # Check if token is expired
        token_data = user_tokens[user_id]
        if datetime.datetime.utcnow() > token_data.get('expires_at', datetime.datetime.min):
            return jsonify({'valid': False, 'message': 'Token expired'}), 401
        
        # Token is valid
        user_info = token_data.get('user_info', {})
        return jsonify({
            'valid': True,
            'user': {
                'id': user_id,
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'picture': user_info.get('picture')
            }
        }), 200

    @app.route("/", methods=["GET"])
    @auth_required
    def home(user_id):
        # Validate that request is coming from our extension
        if not validate_extension_request():
            logger.warning(f"Unauthorized request from {request.remote_addr}")
            return jsonify({"message": "Unauthorized request"}), 403
            
        yt_url = request.args.get("yt_url")
        keyword = request.args.get("keyword")
        
        if not yt_url or not keyword:
            logger.warning(f"Missing parameters in request from {request.remote_addr}")
            return jsonify({"message": "Missing required parameters"}), 400
            
        # Validate YouTube URL using comprehensive validation
        if not is_valid_youtube_url(yt_url):
            logger.warning(f"Invalid YouTube URL: {yt_url}")
            return jsonify({"message": "Invalid YouTube URL format. Please provide a valid YouTube URL."}), 400
            
        # Extract the video ID for additional validation and logging
        video_id = extract_video_id(yt_url)
        if not video_id:
            logger.warning(f"Could not extract video ID from URL: {yt_url}")
            return jsonify({"message": "Could not extract YouTube video ID from the provided URL."}), 400
            
        # Get user information
        user_info = user_tokens[user_id].get('user_info', {})
        user_email = user_info.get('email', 'unknown')
            
        logger.info(f"Processing request for video ID: {video_id}, keyword: {keyword} by user: {user_email}")
        
        # Use the validated video ID for processing
        # For yt-dlp, we should still use the full URL
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
        # Health check can be public for monitoring
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
