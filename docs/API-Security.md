# API Security for Vidify

This document outlines the API security measures implemented to protect our backend services from unauthorized access.

## Overview

To reduce call rates and GCP costs, we've implemented a token-based authentication system that ensures only our Chrome extension can call the remotely hosted API. All other requests are denied.

## Implementation Details

### Authentication Method

- **Type**: API Key-based authentication
- **Header Name**: `X-API-Key`
- **Location**: The API key is included in the HTTP headers of each request

### Security Measures

1. **Fixed API Key**: A pre-shared API key is embedded in both the Chrome extension and the backend.
2. **Request Validation**: Every API endpoint validates the API key before processing the request.
3. **Unauthorized Access**: Requests without a valid API key receive a 401 Unauthorized response.

### API Endpoints Protected

- `/object_search` - Searches for objects in YouTube videos
- `/transcript_search` - Searches YouTube video transcripts

## For Developers

### Adding New Endpoints

When adding new endpoints to the API, ensure you include the API key validation:

```python
@app.route("/new_endpoint", methods=["GET"])
def new_endpoint():
    # Validate API key first
    if not validate_api_key():
        return jsonify({"message": "Unauthorized. Invalid or missing API key."}), 401
        
    # Continue with endpoint logic
    # ...
```

### Making API Calls

When making API calls from the extension, always include the API key:

```javascript
const response = await fetch(apiUrl, {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY
  },
  mode: 'cors',
});
```

## Security Considerations

- In a production environment, consider using environment variables for storing API keys
- Consider implementing key rotation or expiry for additional security
- To further enhance security, consider implementing CORS restrictions
- For production systems, consider using OAuth or JWT-based authentication for more robust security