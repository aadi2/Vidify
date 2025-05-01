# Vidify API Security Implementation

## Overview

To ensure that only our official Chrome extension can use the Vidify backend API, we've implemented API key authentication. This document explains the security measures in place and how they work.

## API Key Authentication

All API endpoints in the Vidify backend are now protected with API key authentication:

```
GET /any-endpoint
X-API-Key: your-api-key-here
```

### How It Works

1. **API Key Generation**: A secure, random API key is generated and shared between the backend and extension
2. **Backend Validation**: The Flask backend checks for a valid API key in the `X-API-Key` header for all requests
3. **Extension Integration**: The Chrome extension includes this API key in all its API requests
4. **Access Control**: Requests without a valid API key receive a 401 Unauthorized response

### Security Benefits

- **Reduced Costs**: Prevents unauthorized third parties from consuming API resources
- **Abuse Prevention**: Blocks potential misuse or excessive requests to the API
- **Service Reliability**: Helps maintain service availability for legitimate users

## Implementation Details

### Backend (Flask)

Our Flask application uses a decorator pattern to validate the API key on all endpoints:

```python
@app.route("/endpoint")
@require_api_key  # This decorator validates the API key
def endpoint_function():
    # Function only runs if API key is valid
    pass
```

### Chrome Extension

The extension maintains the API key as a constant and includes it in all fetch requests:

```javascript
const API_KEY = "your-api-key-here";

// API request
const response = await fetch(apiUrl, {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,  // API key included in header
  },
  mode: 'cors',
});
```

## Security Considerations

- The API key is stored in the extension's code and backend code, not exposed to end users
- While this approach is suitable for preventing casual API misuse, it's not a complete solution for all security threats
- The API key should be rotated periodically for enhanced security

## Testing

A test script is available in `/test/backend_test/api_key_test.py` to verify the API key authentication works correctly.