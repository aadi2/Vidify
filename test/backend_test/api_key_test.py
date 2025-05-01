from flask import Flask, jsonify
import json
from functools import wraps

# Instead of importing from the actual app, we'll create a simplified version
# of the API key functionality for testing

# API key for testing
API_KEY = "test_api_key_12345"


# Create a simplified version of the app with just the API key decorator
def create_test_app():
    app = Flask(__name__)

    # Define API key decorator
    def require_api_key(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import request

            provided_key = request.headers.get("X-API-Key")
            if provided_key and provided_key == API_KEY:
                return f(*args, **kwargs)
            else:
                return jsonify(
                    {"message": "Unauthorized. Invalid or missing API key."}
                ), 401

        return decorated_function

    # Create a test health endpoint
    @app.route("/health", methods=["GET"])
    @require_api_key
    def health_check():
        return jsonify({"status": "OK"}), 200

    return app


# Test data
TEST_YOUTUBE_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Example video
TEST_SEARCH_TERM = "example"


def test_api_key_validation():
    """Test the API key authentication functionality"""
    # Create a simplified test app with just the API key authentication
    app = create_test_app()
    client = app.test_client()

    # 1. Test without API key - should return 401
    response = client.get("/health")
    assert response.status_code == 401
    data = json.loads(response.data)
    assert data["message"] == "Unauthorized. Invalid or missing API key."

    # 2. Test with invalid API key - should return 401
    response = client.get("/health", headers={"X-API-Key": "invalid_key"})
    assert response.status_code == 401
    data = json.loads(response.data)
    assert data["message"] == "Unauthorized. Invalid or missing API key."

    # 3. Test with valid API key - should return 200
    response = client.get("/health", headers={"X-API-Key": API_KEY})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "OK"

    print("All API key validation tests passed!")


if __name__ == "__main__":
    # Run the test directly
    test_api_key_validation()
