# Vidify: User Manual & API Documentation

## Table of Contents

1. [User Manual](#user-manual)
   - [Installation](#installation)
   - [Getting Started](#getting-started)
   - [Using the Extension](#using-the-extension)
   - [Troubleshooting](#troubleshooting)
2. [API Documentation](#api-documentation)
   - [Backend API Endpoints](#backend-api-endpoints)
   - [Extension API](#extension-api)
   - [Data Models](#data-models)

---

# User Manual

## Installation

### Chrome Web Store (Coming Soon)
1. Navigate to the Chrome Web Store
2. Search for "Vidify"
3. Click "Add to Chrome"
4. Confirm the installation when prompted

### Manual Installation
1. Download the latest release from our GitHub repository
2. Extract the zip file to a location on your computer
3. Open Chrome and navigate to `chrome://extensions/`
4. Enable "Developer mode" in the top-right corner
5. Click "Load unpacked" and select the extracted extension folder
6. The Vidify extension should now appear in your browser toolbar

## Getting Started

### Extension Access
There are two ways to access Vidify:
1. **Popup Mode**: Click the Vidify icon in the Chrome toolbar
2. **Side Panel Mode**: Click the side panel icon in Chrome and select Vidify

### Interface Overview
The Vidify interface consists of:
- Search input field for entering keywords
- Search button to initiate the search
- Toggle switches for dark mode and search mode
- Results area displaying timestamps and matched content

## Using the Extension

### Basic Transcript Search
1. Navigate to any YouTube video
2. Open Vidify either via the toolbar icon or side panel
3. Enter a keyword or phrase in the search field
4. Click the "Search" button
5. View the results, which include timestamps and context where the keyword appears

### Search Modes
Vidify currently supports:
- **Transcript Search**: Finds keywords mentioned in the video's transcript/captions
- **Object Detection**: (Coming soon) Will identify when specific objects appear visually

### Customizing Your Experience
- **Dark Mode**: Toggle the "Dark Mode" switch for a darker interface
- **Search Mode**: Toggle between transcript search and object detection (when available)

### Viewing Results
- Results appear in a scrollable list
- Each result shows the timestamp and the text context where your search term was found
- Your search term will be highlighted within the result text
- (Coming soon) Clicking on a result will navigate to that timestamp in the video

## Troubleshooting

### Common Issues

#### "Invalid YouTube URL"
- Make sure you're on a YouTube video page
- Check that the URL is in the correct format (youtube.com/watch?v=...)

#### "No results found"
- Try searching for different keywords
- Ensure the video has captions available
- If searching in a language other than English, try English keywords

#### "Not able to fetch transcript"
- Some videos may not have transcripts/captions available
- Try a different video that has captions

#### Extension Not Working
1. Check if you're on a compatible YouTube page
2. Verify your internet connection
3. Refresh the page
4. If issues persist, reinstall the extension

### Support
If you continue to experience issues:
- Check our GitHub Issues page for known problems
- Submit a new issue with detailed information about your problem
- Include your browser version and operating system

---

# API Documentation

## Backend API Endpoints

Vidify's backend API is not publicly accessible to reduce operational costs. The following documentation is for development and reference purposes only.

### Health Check
```
GET /health
```
- Purpose: Verify the API is operational
- Response: `{"status": "OK"}`
- Status codes: 
  - 200: API is operational

### Transcript Search
```
GET /transcript_search
```
- Purpose: Search for keywords in a video's transcript
- Parameters:
  - `yt_url` (required): YouTube video ID or full URL
  - `keyword` (required): Term to search for in the transcript
- Response:
  ```json
  {
    "message": "Transcript downloaded successfully.",
    "results": [
      {"timestamp": "0:12", "text": "This is a sample text containing the keyword"},
      {"timestamp": "1:45", "text": "Another occurrence of the keyword in context"}
    ]
  }
  ```
- Status codes:
  - 200: Search successful
  - 400: Invalid YouTube URL
  - 404: Transcript not available
  - 500: Internal server error

### Object Search (Coming Soon)
```
GET /object_search
```
- Purpose: Detect objects in a video
- Parameters:
  - `yt_url` (required): YouTube video ID or full URL
  - `keyword` (required): Object to locate in the video
- Response:
  ```json
  {
    "message": "Objects detected successfully.",
    "results": [
      {"timestamp": "0:12", "object": "detected object"},
      {"timestamp": "1:45", "object": "detected object"}
    ]
  }
  ```
- Status codes:
  - 200: Search successful
  - 400: Invalid YouTube URL
  - 404: Not implemented yet or video not available
  - 500: Internal server error

## Extension API

The Vidify extension exposes several message handlers for communication between components.

### Background Service Worker

#### Message Handlers
The background service worker listens for the following messages:

##### Search Transcript
```javascript
chrome.runtime.sendMessage({
  action: "searchTranscript",
  videoId: "<YouTube Video ID>",
  searchTerm: "<Search Term>"
}, response => {
  // Handle response
});
```

##### Search Objects
```javascript
chrome.runtime.sendMessage({
  action: "searchObjects",
  videoId: "<YouTube Video ID>",
  searchTerm: "<Search Term>"
}, response => {
  // Handle response
});
```

##### Get Search History
```javascript
chrome.runtime.sendMessage({
  action: "getSearchHistory"
}, response => {
  // Handle response with search history
});
```

### Content Script API

The content script provides functions to interact with the YouTube player:

#### Display Results
```javascript
chrome.runtime.sendMessage({
  action: "displayResults",
  data: [
    { timestamp: "1:23", text: "Result text" }
  ]
});
```

#### Navigate to Timestamp
```javascript
// Implemented in content.js
function seekToTimestamp(timestamp) {
  // Seeks the video to the specified timestamp
}
```

## Data Models

### Search Result
```json
{
  "timestamp": "string", // Format: "MM:SS" or seconds
  "text": "string"       // The matching text context
}
```

### Object Detection Result (Future)
```json
{
  "timestamp": "string", // Format: "MM:SS" or seconds
  "object": "string"     // The detected object name
}
```

### Transcript Format
The backend uses WebVTT format for transcripts. Example:
```
WEBVTT

00:00:01.000 --> 00:00:05.000
This is the first caption text.

00:00:05.500 --> 00:00:08.000
This is the second caption text.
```

---

This documentation is subject to updates as Vidify continues to evolve. For the latest information, please check our GitHub repository.
