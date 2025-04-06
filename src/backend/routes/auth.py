import os
import jwt
import datetime
import logging
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
from middlewares.auth_middleware import validate_extension

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger("auth")

# Create a blueprint for auth routes
auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/token", methods=["POST"])
@validate_extension
def generate_token():
    """
    Generate a JWT token for authenticated API access.
    
    Returns:
        JSON response containing token and expiration time.
    """
    try:
        # Get JWT configuration from environment
        jwt_secret_key = os.getenv('JWT_SECRET_KEY', 'default_secret_key_for_development')
        jwt_expires = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 86400))  # 24 hours
        
        # Create token with expiration time
        expiration = datetime.datetime.utcnow() + datetime.timedelta(seconds=jwt_expires)
        
        payload = {
            'exp': expiration,
            'iat': datetime.datetime.utcnow(),
            'sub': 'extension_user',  # Subject (user identifier)
        }
        
        token = jwt.encode(
            payload,
            jwt_secret_key,
            algorithm="HS256"
        )
        
        logger.info(f"Token generated for extension: {request.headers.get('X-Extension-Id')}")
        return jsonify({
            'token': token,
            'expires_at': expiration.timestamp()
        }), 200
        
    except Exception as e:
        logger.error(f"Token generation error: {str(e)}")
        return jsonify({'message': 'Error generating token'}), 500