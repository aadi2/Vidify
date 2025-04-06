const API_URL = "https://vidify-378225991600.us-central1.run.app"

// Keep track of the authentication token and its expiration
let authToken = null;
let tokenExpiration = null;
let userProfile = null;

// Automatically trigger authentication check when the extension is installed or started.
chrome.runtime.onInstalled.addListener(() => {
    console.log("Vidify extension installed and ready!");
    checkAuthentication();
  });
  
  chrome.runtime.onStartup.addListener(() => {
    console.log("Vidify extension started.");
    checkAuthentication();
  });

/**
 * Checks if the user is already authenticated
 */
async function checkAuthentication() {
  try {
    const storedData = await chrome.storage.local.get(['authToken', 'tokenExpiration', 'userProfile']);
    
    // Check if we have a stored token
    if (storedData.authToken && storedData.tokenExpiration) {
      const now = new Date().getTime();
      const expiry = new Date(storedData.tokenExpiration).getTime();
      
      if (now < expiry - 60000) { // 1 minute buffer
        console.log("Using stored authentication token");
        authToken = storedData.authToken;
        tokenExpiration = storedData.tokenExpiration;
        userProfile = storedData.userProfile;
        
        // Validate token with the server
        const isValid = await validateToken(authToken);
        if (isValid) {
          return true;
        }
      }
    }
    
    // Clear any invalid or expired token
    authToken = null;
    tokenExpiration = null;
    userProfile = null;
    
    await chrome.storage.local.remove(['authToken', 'tokenExpiration', 'userProfile']);
    return false;
    
  } catch (error) {
    console.error("Authentication check error:", error);
    return false;
  }
}

/**
 * Validates a token with the server
 */
async function validateToken(token) {
  try {
    const extensionId = chrome.runtime.id;
    const response = await fetch(`${API_URL}/auth/validate`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-Extension-Id': extensionId,
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) {
      return false;
    }
    
    const data = await response.json();
    if (data.valid && data.user) {
      userProfile = data.user;
      await chrome.storage.local.set({ userProfile });
      return true;
    }
    
    return false;
  } catch (error) {
    console.error("Token validation error:", error);
    return false;
  }
}

/**
 * Initiates the OAuth authentication flow
 */
async function authenticateUser() {
  try {
    // Check if we're already authenticated
    const isAuthenticated = await checkAuthentication();
    if (isAuthenticated) {
      return true;
    }
    
    // Open a popup for Google OAuth authentication
    const extensionId = chrome.runtime.id;
    const authUrl = `${API_URL}/auth/login`;
    
    // Calculate center position for the popup
    const width = 800;
    const height = 600;
    const left = (screen.width - width) / 2;
    const top = (screen.height - height) / 2;
    
    const authWindow = window.open(
      authUrl, 
      'Vidify Authentication',
      `width=${width},height=${height},left=${left},top=${top}`
    );
    
    // Set up message listener for the token
    return new Promise((resolve, reject) => {
      const messageListener = async (event) => {
        if (event.data && event.data.type === 'vidify_auth_token') {
          // Remove the event listener
          window.removeEventListener('message', messageListener);
          
          // Save the token
          authToken = event.data.token;
          tokenExpiration = new Date(event.data.expires_at);
          
          // Validate and store the token
          const isValid = await validateToken(authToken);
          if (isValid) {
            await chrome.storage.local.set({
              authToken,
              tokenExpiration: tokenExpiration.toISOString(),
              userProfile
            });
            
            resolve(true);
          } else {
            reject(new Error('Token validation failed'));
          }
        }
      };
      
      window.addEventListener('message', messageListener);
      
      // Set timeout in case the window is closed without completing auth
      setTimeout(() => {
        window.removeEventListener('message', messageListener);
        reject(new Error('Authentication timed out'));
      }, 300000); // 5 minutes timeout
    });
    
  } catch (error) {
    console.error("Authentication error:", error);
    throw error;
  }
}

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
                handleTranscriptSearch(request.videoId, request.searchTerm).then((response) => sendResponse(response))
                return true;
                break;

            case "getSearchHistory":
                handleSearchHistory(sendResponse);
                break;
            
            case "fetchFromSPI":
                fetchFromSPI(request.endpoint, request.payload, sendResponse);
                break;
                
            case "checkAuth":
                checkAuthentication().then(isAuthenticated => {
                    sendResponse({ 
                        isAuthenticated, 
                        userProfile: userProfile || null 
                    });
                });
                return true;
                break;
                
            case "login":
                authenticateUser().then(success => {
                    sendResponse({ 
                        success, 
                        userProfile: userProfile || null 
                    });
                }).catch(error => {
                    sendResponse({ 
                        success: false, 
                        error: error.message 
                    });
                });
                return true;
                break;
                
            case "logout":
                // Clear stored authentication data
                authToken = null;
                tokenExpiration = null;
                userProfile = null;
                chrome.storage.local.remove(['authToken', 'tokenExpiration', 'userProfile'])
                    .then(() => {
                        sendResponse({ success: true });
                    })
                    .catch(error => {
                        sendResponse({ success: false, error: error.message });
                    });
                return true;
                break;

            default:
                console.warn("Unknown action received: ", request.action);
                sendResponse({ status: "Unknown action" });
        }
    } catch (error) {
        console.error("Error processing request: ", error);
        sendResponse({ status: "Error", message: error.message });
    }

    // Required to keep the sendResponse callback open for asynchronous use
    return true;
});

/**
 * Checks if a URL is a YouTube video URL.
 */
function isYouTubeVideoURL(url) {
    if (!url) return false;
    
    // Check for common YouTube URL patterns
    const youtubePatterns = [
        /youtube\.com\/watch\?v=[a-zA-Z0-9_-]{11}/,
        /youtu\.be\/[a-zA-Z0-9_-]{11}/,
        /youtube\.com\/embed\/[a-zA-Z0-9_-]{11}/,
        /youtube\.com\/shorts\/[a-zA-Z0-9_-]{11}/
    ];
    
    return youtubePatterns.some(pattern => pattern.test(url));
}

/**
 * Extracts the YouTube video ID from a URL.
 */
function extractYouTubeVideoID(url) {
    // Handle youtu.be URLs
    let match = url.match(/youtu\.be\/([a-zA-Z0-9_-]{11})(?:\?|\/|$)/);
    if (match) {
        return match[1];
    }
    
    // Handle youtube.com/watch URLs
    match = url.match(/[?&]v=([a-zA-Z0-9_-]{11})(?:&|$|#)/);
    if (match) {
        return match[1];
    }
    
    // Handle youtube.com/embed URLs
    match = url.match(/youtube\.com\/embed\/([a-zA-Z0-9_-]{11})(?:\?|\/|$)/);
    if (match) {
        return match[1];
    }
    
    // Handle youtube.com/shorts URLs
    match = url.match(/youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})(?:\?|\/|$)/);
    if (match) {
        return match[1];
    }
    
    // Handle classic URL pattern as a fallback
    match = url.match(/[?&]v=([^&]+)/) || url.match(/youtu\.be\/([^?]+)/);
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
 * Performs an authenticated fetch call using the stored access token.
 */
async function authenticatedFetch(url, payload) {
    const result = await chrome.storage.local.get(["accessToken"]);
    const accessToken = result.accessToken;
    if (!accessToken) {
        return { status: "error", message: "User not authenticated" };
    }
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${accessToken}`
        },
        body: JSON.stringify(payload)
    });
    return response.json();
}

/**
 * Handles transcript search by making an API call to the backend.
 * @param {string} videoId - YouTube video ID
 * @param {string} searchTerm - Keyword or phrase to search in the transcript
 * @param {function} sendResponse - Function to send response back to the caller
 */
async function handleTranscriptSearch(videoId, searchTerm) {
    //const finalVideoId = await getCurrentVideoId(videoId);
    console.log(`videoID: ${videoId}`);
  
    if (!videoId) {
      return { status: "error", message: "No video detected or provided" };
      return;
    }
    
    // Ensure we have a valid authentication token
    const isAuthenticated = await checkAuthentication();
    if (!isAuthenticated) {
      try {
        // Attempt to authenticate the user
        await authenticateUser();
      } catch (error) {
        return { status: "error", message: "Authentication required. Please sign in." };
      }
    }
    
    if (!authToken) {
      return { status: "error", message: "Authentication failed" };
    }
  
    try {
      console.log(`Searching for term: ${searchTerm} in video: ${videoId}`);
  
      const apiUrl = API_URL + "/?yt_url=" + videoId + "&keyword=" + searchTerm;

      // Get extension ID to send in headers for authentication
      const extensionId = chrome.runtime.id;
      
      //console.log(`API url`, apiUrl);
      const response = await fetch(apiUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Extension-Id': extensionId,
          'Authorization': `Bearer ${authToken}`
        },
        mode: 'cors',
      })

  
      console.log("HTTP Status:", response.status, response.statusText);
      const rawText = await response.text();
      console.log("Raw response text:", rawText);
  
      let result;
      try {
        result = JSON.parse(rawText);
      } catch (parseError) {
        throw new Error(`Failed to parse JSON response: ${rawText}`);
      }
  
      if (response.ok) {
        console.log("Transcript search successful:", result);
        return { status: "success", data: result };
      } else {
        throw new Error(result.message || `Transcript search failed with status ${response.status} ${response.statusText}`);
      }
    } catch (error) {
      console.error("Transcript search error:", error);
      return { status: "error", message: error.message };
    }
  }
  

/**
 * Handles retrieval of the user's search history from Chrome storage.
 * @param {function} sendResponse - Function to send response back to the caller
 */
function handleSearchHistory(sendResponse) {
    chrome.storage.local.get(["searchHistory"], (result) => {
        if (result.searchHistory) {
            console.log("Returning search history:", result.searchHistory);
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
    
    // Ensure we have a valid authentication token
    const isAuthenticated = await checkAuthentication();
    if (!isAuthenticated) {
        try {
            // Attempt to authenticate the user
            await authenticateUser();
        } catch (error) {
            sendResponse({ status: "error", message: "Authentication required. Please sign in." });
            return;
        }
    }
    
    if (!authToken) {
        sendResponse({ status: "error", message: "Authentication failed" });
        return;
    }

    try {
        const apiUrl = `http://localhost:5000${endpoint}`;
        const requestBody = { ...payload, videoId: finalVideoId };  // Auto-add videoId if not in payload
        
        // Get extension ID to send in headers for authentication
        const extensionId = chrome.runtime.id;

        const response = await fetch(apiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Extension-Id": extensionId,
                "Authorization": `Bearer ${authToken}`
            },
            body: JSON.stringify(requestBody)
        });

        const result = await response.json();

        if (response.ok) {
            sendResponse({ status: "success", data: result });
        } else {
            throw new Error(result.message || "SPI request failed.");
        }
    } catch (error) {
        console.error("SPI request error:", error);
        sendResponse({ status: "error", message: error.message });
    }
}
