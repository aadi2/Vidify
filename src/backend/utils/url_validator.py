"""
URL Validator module for validating YouTube URLs.
"""
import re
from urllib.parse import urlparse, parse_qs
import logging

# Configure logging
logger = logging.getLogger("url_validator")

# Regular expressions for YouTube URLs
# Matches standard youtube.com/watch URLs
YOUTUBE_WATCH_PATTERN = r'^(https?://)?(www\.)?(youtube\.com/watch\?v=)([a-zA-Z0-9_-]{11})(\S*)?$'

# Matches short youtu.be URLs 
YOUTUBE_SHORT_PATTERN = r'^(https?://)?(www\.)?(youtu\.be/)([a-zA-Z0-9_-]{11})(\S*)?$'

# Matches YouTube embed URLs
YOUTUBE_EMBED_PATTERN = r'^(https?://)?(www\.)?(youtube\.com/embed/)([a-zA-Z0-9_-]{11})(\S*)?$'

# Matches YouTube shortened URLs with timestamps
YOUTUBE_TIMESTAMP_PATTERN = r'^(https?://)?(www\.)?(youtube\.com/shorts/)([a-zA-Z0-9_-]{11})(\S*)?$'

def is_valid_youtube_url(url):
    """
    Validates if a URL is a valid YouTube URL.
    
    Args:
        url (str): The URL to validate.
        
    Returns:
        bool: True if the URL is a valid YouTube URL, False otherwise.
    """
    if not url:
        logger.warning("Empty URL provided")
        return False
    
    # First check for malicious patterns before even matching against YouTube patterns
    dangerous_patterns = [
        "<",  # Catch all HTML tags including <script>
        ">",
        "javascript:",
        "data:",
        "file:"
    ]
    
    for pattern in dangerous_patterns:
        if pattern in url:
            logger.warning(f"Potentially malicious URL detected: {url}")
            return False
    
    # Check against regex patterns
    patterns = [
        YOUTUBE_WATCH_PATTERN,
        YOUTUBE_SHORT_PATTERN,
        YOUTUBE_EMBED_PATTERN,
        YOUTUBE_TIMESTAMP_PATTERN
    ]
    
    for pattern in patterns:
        if re.match(pattern, url):
            return True
            
    # Check if URL has a valid scheme/protocol
    if not url.startswith(('http://', 'https://')):
        logger.warning(f"Invalid URL protocol: {url}")
        return False
        
    # Additional validation for URLs that might not match the regex
    try:
        parsed_url = urlparse(url)
        
        # Check domain
        if parsed_url.netloc not in ['youtube.com', 'www.youtube.com', 'youtu.be', 'www.youtu.be']:
            logger.warning(f"Invalid YouTube domain: {parsed_url.netloc}")
            return False
        
        # For youtube.com URLs, ensure there's a video ID parameter
        if 'youtube.com' in parsed_url.netloc:
            if parsed_url.path == '/watch':
                query_params = parse_qs(parsed_url.query)
                if 'v' not in query_params or not query_params['v'][0]:
                    logger.warning("Missing or empty video ID in YouTube URL")
                    return False
                # Check video ID length (YouTube IDs are usually 11 characters)
                if len(query_params['v'][0]) != 11:
                    logger.warning(f"Unusual video ID length: {len(query_params['v'][0])}")
                    # Not returning false here as YouTube IDs might change format
            elif not any(path in parsed_url.path for path in ['/embed/', '/shorts/']):
                logger.warning(f"Unrecognized YouTube URL path: {parsed_url.path}")
                return False
        
        # For youtu.be URLs, ensure there's a path (which is the video ID)
        elif 'youtu.be' in parsed_url.netloc:
            if not parsed_url.path or parsed_url.path == '/':
                logger.warning("Missing video ID in youtu.be URL")
                return False
            # Check video ID length
            if len(parsed_url.path.strip('/')) != 11:
                logger.warning(f"Unusual video ID length in youtu.be URL: {len(parsed_url.path.strip('/'))}")
                # Not returning false here as YouTube IDs might change format
        
        return True
    
    except Exception as e:
        logger.error(f"Error parsing URL: {str(e)}")
        return False

def extract_video_id(url):
    """
    Extracts the video ID from a YouTube URL.
    
    Args:
        url (str): The YouTube URL.
        
    Returns:
        str or None: The video ID if found, None otherwise.
    """
    if not is_valid_youtube_url(url):
        return None
    
    try:
        parsed_url = urlparse(url)
        
        # Handle youtu.be URLs
        if 'youtu.be' in parsed_url.netloc:
            return parsed_url.path.strip('/')
        
        # Handle youtube.com URLs
        if 'youtube.com' in parsed_url.netloc:
            if parsed_url.path == '/watch':
                query_params = parse_qs(parsed_url.query)
                return query_params.get('v', [None])[0]
            elif '/embed/' in parsed_url.path:
                return parsed_url.path.split('/embed/')[1].split('/')[0]
            elif '/shorts/' in parsed_url.path:
                return parsed_url.path.split('/shorts/')[1].split('/')[0]
        
        return None
    
    except Exception as e:
        logger.error(f"Error extracting video ID: {str(e)}")
        return None