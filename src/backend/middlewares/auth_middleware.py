import os
import jwt
import logging
from functools import wraps
from flask import jsonify, request
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger("auth")

def token_required(f):
    """
    Decorator to validate JWT tokens in request headers.
    
    Args:
        f: The function to wrap.
        
    Returns:
        The decorated function.
    """
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
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            # Get secret key from environment
            jwt_secret_key = os.getenv('JWT_SECRET_KEY', 'default_secret_key_for_development')
            
            # Decode the token
            data = jwt.decode(token, jwt_secret_key, algorithms=["HS256"])
            current_user = data['sub']  # 'sub' is the subject of the token (usually user_id)
        except jwt.ExpiredSignatureError:
            logger.warning(f"Expired token used: {request.remote_addr}")
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            logger.warning(f"Invalid token used: {request.remote_addr}")
            return jsonify({'message': 'Invalid token'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

def validate_extension(f):
    """
    Decorator to validate that requests are coming from the Chrome extension.
    
    Args:
        f: The function to wrap.
        
    Returns:
        The decorated function.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check if the request includes Chrome extension ID in headers
        extension_id = request.headers.get('X-Extension-Id')
        valid_extension_id = os.getenv('VALID_EXTENSION_ID', 'your_chrome_extension_id')
        
        if not extension_id or extension_id != valid_extension_id:
            logger.warning(f"Invalid extension ID: {extension_id} from {request.remote_addr}")
            return jsonify({"message": "Unauthorized request"}), 403
            
        return f(*args, **kwargs)
    return decorated