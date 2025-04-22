const API_URL = "https://vidify-378225991600.us-central1.run.app";

// Create a cache for API responses
class ApiCache {
    constructor(cacheTimeoutMs = 900000) { // 15 minutes cache timeout
        this.cache = {};
        this.timeoutMs = cacheTimeoutMs;
        
        // Cleanup interval - check cache every 5 minutes
        this.cleanupInterval = setInterval(() => this.cleanup(), 300000);
    }
    
    // Get a cached value or null if not found
    get(key) {
        const cachedItem = this.cache[key];
        if (cachedItem && Date.now() - cachedItem.timestamp < this.timeoutMs) {
            console.log(`Cache hit for ${key}`);
            return cachedItem.data;
        }
        return null;
    }
    
    // Store a value in the cache
    set(key, data) {
        this.cache[key] = {
            data,
            timestamp: Date.now()
        };
    }
    
    // Clean up expired entries
    cleanup() {
        const now = Date.now();
        for (const key in this.cache) {
            if (now - this.cache[key].timestamp > this.timeoutMs) {
                console.log(`Removing expired cache entry: ${key}`);
                delete this.cache[key];
            }
        }
    }
    
    // Clear specific entry
    clear(key) {
        delete this.cache[key];
    }
    
    // Clear all entries
    clearAll() {
        this.cache = {};
    }
}

// Create HTTP session manager with reuse
class HttpSessionManager {
    constructor() {
        // Dummy implementation for browser extension
        // In a real environment, this would manage request connections
        this.headers = {
            'Content-Type': 'application/json',
            'mode': 'cors'
        };
    }
    
    // Get headers with any additional headers
    getHeaders(additionalHeaders = {}) {
        return {...this.headers, ...additionalHeaders};
    }
}

// Initialize managers
const apiCache = new ApiCache();
const sessionManager = new HttpSessionManager();

// Automatically trigger authentication when the extension is installed or started.
chrome.runtime.onInstalled.addListener(() => {
    console.log("Vidify extension installed and ready!");
    //ensureAuthenticated();
});
  
chrome.runtime.onStartup.addListener(() => {
    console.log("Vidify extension started.");
    //ensureAuthenticated();
});

// Detect YouTube video URL and store videoId in chrome.storage.local
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.url && isYouTubeVideoURL(changeInfo.url)) {
        const videoId = extractYouTubeVideoID(changeInfo.url);
        if (videoId) {
            console.log(`Detected YouTube video: ${videoId}`);
            chrome.storage.local.set({ currentVideoId: videoId }, () => {
                console.log(`Stored video ID: ${videoId}`);
            });
        }
    }
});

/**
 * Listen for messages from content scripts or the extension popup
 * Handles requests such as object detection, transcript search, and search history
 */
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    try {
        switch (request.action) {
            case "searchTranscript":
                handleTranscriptSearch(request.videoId, request.searchTerm)
                    .then(sendResponse)
                    .catch(error => {
                        console.error("Error in transcript search:", error);
                        sendResponse({
                            status: "error",
                            message: error.message || "Unknown error in transcript search"
                        });
                    });
                return true;

            case "searchObjects":
                handleObjectSearch(request.videoId, request.searchTerm)
                    .then(sendResponse)
                    .catch(error => {
                        console.error("Error in object search:", error);
                        sendResponse({
                            status: "error",
                            message: error.message || "Unknown error in object search"
                        });
                    });
                return true;

            case "getSearchHistory":
                handleSearchHistory(sendResponse);
                return true;
            
            case "fetchFromSPI":
                fetchFromSPI(request.endpoint, request.payload, sendResponse);
                return true;

            case "clearCache":
                apiCache.clearAll();
                sendResponse({ status: "success", message: "Cache cleared" });
                return false;

            default:
                console.warn("Unknown action received: ", request.action);
                sendResponse({ status: "error", message: "Unknown action" });
                return false;
        }
    } catch (error) {
        console.error("Error processing request: ", error);
        sendResponse({ status: "error", message: error.message });
        return false;
    }
});

/**
 * Checks if a URL is a YouTube video URL.
 */
function isYouTubeVideoURL(url) {
    return url.includes("youtube.com/watch") || url.includes("youtu.be/");
}

/**
 * Extracts the YouTube video ID from a URL.
 */
function extractYouTubeVideoID(url) {
    const match = url.match(/[?&]v=([^&]+)/) || url.match(/youtu\.be\/([^?]+)/);
    return match ? match[1] : null;
}

/**
 * Gets the current video ID from the provided parameter or from storage.
 */
async function getCurrentVideoId(providedVideoId) {
    if (providedVideoId) {
        return providedVideoId;  // Prefer directly provided videoId
    }
    const result = await chrome.storage.local.get(["currentVideoId"]);
    return result.currentVideoId || null;  // Fallback to stored videoId
}

/**
 * Handles transcript search by making an API call to the backend.
 * @param {string} videoId - YouTube video ID
 * @param {string} searchTerm - Keyword or phrase to search in the transcript
 */
async function handleTranscriptSearch(videoId, searchTerm) {
    console.log(`videoID: ${videoId}`);
  
    if (!videoId) {
        return { status: "error", message: "No video detected or provided" };
    }
    
    // Generate cache key
    const cacheKey = `transcript_${videoId}_${searchTerm}`;
    
    // Check cache first
    const cachedResult = apiCache.get(cacheKey);
    if (cachedResult) {
        return { status: "success", data: cachedResult };
    }
  
    try {
        console.log(`Searching for term: ${searchTerm} in transcript: ${videoId}`);
  
        const apiUrl = `${API_URL}/transcript_search?yt_url=${encodeURIComponent(videoId)}&keyword=${encodeURIComponent(searchTerm)}`;

        // Use fetch with timeout to avoid hanging requests
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
        
        const response = await fetch(apiUrl, {
            method: 'GET',
            headers: sessionManager.getHeaders(),
            signal: controller.signal
        });
        
        // Clear timeout
        clearTimeout(timeoutId);
  
        console.log("HTTP Status:", response.status, response.statusText);
        const rawText = await response.text();
        
        let result;
        try {
            result = JSON.parse(rawText);
        } catch (parseError) {
            throw new Error(`Failed to parse JSON response: ${rawText}`);
        }
  
        if (response.ok) {
            console.log("Transcript search successful");
            
            // Cache successful results
            apiCache.set(cacheKey, result);
            
            // Store in search history
            storeSearchResult({
                type: "transcript",
                videoId,
                searchTerm,
                timestamp: Date.now(),
                resultCount: result.results ? result.results.length : 0
            });
            
            return { status: "success", data: result };
        } else {
            throw new Error(result.message || `Transcript search failed with status ${response.status} ${response.statusText}`);
        }
    } catch (error) {
        console.error("Transcript search error:", error);
        return { status: "error", message: error.message || "Error during transcript search" };
    }
}

/**
 * Handles object search by making an API call to the backend.
 * @param {string} videoId - YouTube video ID
 * @param {string} searchTerm - Keyword or object to search in the video
 */
async function handleObjectSearch(videoId, searchTerm) {
    console.log(`videoID: ${videoId}`);
  
    if (!videoId) {
        return { status: "error", message: "No video detected or provided" };
    }
    
    // Generate cache key
    const cacheKey = `object_${videoId}_${searchTerm}`;
    
    // Check cache first
    const cachedResult = apiCache.get(cacheKey);
    if (cachedResult) {
        return { status: "success", data: cachedResult };
    }
  
    try {
        console.log(`Searching for object: ${searchTerm} in video: ${videoId}`);
  
        const apiUrl = `${API_URL}/object_search?yt_url=${encodeURIComponent(videoId)}&keyword=${encodeURIComponent(searchTerm)}`;

        // Use fetch with timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout (object detection can take longer)
        
        const response = await fetch(apiUrl, {
            method: 'GET',
            headers: sessionManager.getHeaders(),
            signal: controller.signal
        });
        
        // Clear timeout
        clearTimeout(timeoutId);
  
        console.log("HTTP Status:", response.status, response.statusText);
        const rawText = await response.text();
        
        let result;
        try {
            result = JSON.parse(rawText);
        } catch (parseError) {
            throw new Error(`Failed to parse JSON response: ${rawText}`);
        }
  
        if (response.ok) {
            console.log("Object search successful");
            
            // Cache successful results
            apiCache.set(cacheKey, result);
            
            // Store in search history
            storeSearchResult({
                type: "object",
                videoId,
                searchTerm,
                timestamp: Date.now(),
                resultCount: result.results ? result.results.length : 0
            });
            
            return { status: "success", data: result };
        } else {
            throw new Error(result.message || `Object search failed with status ${response.status} ${response.statusText}`);
        }
    } catch (error) {
        console.error("Object search error:", error);
        return { status: "error", message: error.message || "Error during object search" };
    }
}

/**
 * Handles retrieval of the user's search history from Chrome storage.
 * @param {function} sendResponse - Function to send response back to the caller
 */
function handleSearchHistory(sendResponse) {
    chrome.storage.local.get(["searchHistory"], (result) => {
        if (result.searchHistory) {
            console.log("Returning search history");
            sendResponse({ status: "success", data: result.searchHistory });
        } else {
            console.log("No search history found.");
            sendResponse({ status: "empty", data: [] });
        }
    });
}

/**
 * Utility function to store search results in Chrome local storage
 * for future reference and user convenience.
 * @param {object} searchResult - The search result to store
 */
function storeSearchResult(searchResult) {
    chrome.storage.local.get(["searchHistory"], (result) => {
        let history = result.searchHistory || [];
        
        // Limit history size to 100 entries
        if (history.length >= 100) {
            history = history.slice(-99);
        }
        
        history.push(searchResult);

        chrome.storage.local.set({ searchHistory: history }, () => {
            console.log("Search result stored in history.");
        });
    });
}

/**
 * Generic handler to fetch data from any SPI endpoint.
 */
async function fetchFromSPI(endpoint, payload, sendResponse) {
    const finalVideoId = await getCurrentVideoId(payload.videoId);

    if (!finalVideoId) {
        sendResponse({ status: "error", message: "No video detected or provided" });
        return;
    }

    try {
        const apiUrl = `http://localhost:5000${endpoint}`;
        const requestBody = { ...payload, videoId: finalVideoId };  // Auto-add videoId if not in payload

        // Use fetch with timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
        
        const response = await fetch(apiUrl, {
            method: "POST",
            headers: sessionManager.getHeaders(),
            body: JSON.stringify(requestBody),
            signal: controller.signal
        });
        
        // Clear timeout
        clearTimeout(timeoutId);

        const result = await response.json();

        if (response.ok) {
            sendResponse({ status: "success", data: result });
        } else {
            throw new Error(result.message || "SPI request failed.");
        }
    } catch (error) {
        console.error("SPI request error:", error);
        sendResponse({ status: "error", message: error.message || "Error during SPI request" });
    }
}

// Clean up resources when extension is unloaded
chrome.runtime.onSuspend.addListener(() => {
    console.log("Cleaning up resources");
    if (apiCache) {
        clearInterval(apiCache.cleanupInterval);
    }
});