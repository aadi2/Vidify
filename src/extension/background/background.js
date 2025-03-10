
const GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth";
const REDIRECT_URL = chrome.identity.getRedirectURL();
const CLIENT_ID = "378225991600-ni4cvnivl55g4jbjo1no4de2qaks604b.apps.googleusercontent.com";

const OAUTH_PARAMS = {
    client_id: CLIENT_ID,
    response_type: "token",
    redirect_uri: REDIRECT_URL,
    scope: "https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email"
};

/**
 * Ensures the user is authenticated.
 * If no access token is found, automatically initiates OAuth.
 */
function ensureAuthenticated() {
    chrome.storage.local.get(["accessToken"], (result) => {
      if (!result.accessToken) {
        console.log("No access token found, initiating authentication.");
        startGoogleLogin(() => {});
      } else {
        console.log("User already authenticated.");
      }
    });
  }

// Automatically trigger authentication when the extension is installed or started.
chrome.runtime.onInstalled.addListener(() => {
    console.log("Vidify extension installed and ready!");
    ensureAuthenticated();
  });
  
  chrome.runtime.onStartup.addListener(() => {
    console.log("Vidify extension started.");
    ensureAuthenticated();
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
chrome.runtime.onMessage.addListener(async (request, sender, sendResponse) => {
    try {
        switch (request.action) {
            case "login":
                startGoogleLogin(sendResponse);
                break;

            case "searchObject":
                await handleObjectSearch(request.videoId, request.objectName, sendResponse);
                break;

            case "searchTranscript":
                await handleTranscriptSearch(request.videoId, request.searchTerm, sendResponse);
                break;

            case "getSearchHistory":
                handleSearchHistory(sendResponse);
                break;
            
            case "fetchFromSPI":
                await fetchFromSPI(request.endpoint, request.payload, sendResponse);
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
 * Initiates Google OAuth authentication using Chrome Identity API.
 */
function startGoogleLogin(sendResponse) {
    const authUrl = `${GOOGLE_AUTH_URL}?${new URLSearchParams(OAUTH_PARAMS)}`;

    chrome.identity.launchWebAuthFlow(
        { url: authUrl, interactive: true },
        (redirectUrl) => {
            if (chrome.runtime.lastError) {
                console.error("OAuth failed:", chrome.runtime.lastError);
                sendResponse({ status: "error", message: chrome.runtime.lastError.message });
                return;
            }

            if (redirectUrl) {
                // Extract access token from the redirect URL
                const urlParams = new URLSearchParams(new URL(redirectUrl).hash.substring(1));
                const accessToken = urlParams.get("access_token");

                if (accessToken) {
                    console.log("OAuth successful, token:", accessToken);
                    chrome.storage.local.set({ accessToken }, () => {
                        console.log("Access token saved.");
                    });
                    verifyTokenWithBackend(accessToken);
                    sendResponse({ status: "success", message: "Logged in successfully" });
                }
            }
        }
    );
}

/**
 * Sends the access token to your Flask backend for verification.
 */
function verifyTokenWithBackend(accessToken) {
    fetch("http://localhost:8001/verify-token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ accessToken })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Token verification response:", data);
    })
    .catch(error => {
        console.error("Error verifying token:", error);
    });
}

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
 * Handles object detection search by making an API call to the backend.
 * @param {string} videoId - YouTube video ID
 * @param {string} objectName - Name of the object to search for
 * @param {function} sendResponse - Function to send response back to the caller
 */
async function handleObjectSearch(videoId, objectName, sendResponse) {
    const finalVideoId = await getCurrentVideoId(videoId);

    if (!finalVideoId) {
        sendResponse({ status: "error", message: "No video detected or provided" });
        return;
    }

    try {
        console.log(`Searching for object: ${objectName} in video: ${finalVideoId}`);
        
        const apiUrl = `http://localhost:5000/search/object`;

        const response = await fetch(apiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ videoId: finalVideoId, objectName })
        });

        const result = await response.json();

        if (response.ok) {
            if (validateObjectSearchResponse(result)) {
                console.log("Object detection successful:", result);
                sendResponse({ status: "success", data: result });
            } else {
                throw new Error("Response schema validation failed.");
            }
        } else {
            throw new Error(result.message || "Object detection failed.");
        }
    } catch (error) {
        console.error("Object search error:", error);
        sendResponse({ status: "error", message: error.message });
    }
}

/**
 * Handles transcript search by making an API call to the backend.
 * @param {string} videoId - YouTube video ID
 * @param {string} searchTerm - Keyword or phrase to search in the transcript
 * @param {function} sendResponse - Function to send response back to the caller
 */
async function handleTranscriptSearch(videoId, searchTerm, sendResponse) {
    const finalVideoId = await getCurrentVideoId(videoId);

    if (!finalVideoId) {
        sendResponse({ status: "error", message: "No video detected or provided" });
        return;
    }

    try {
        console.log(`Searching for term: ${searchTerm} in video: ${finalVideoId}`);

        const apiUrl = `http://localhost:5000/search/transcript`;

        const response = await fetch(apiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ videoId: finalVideoId, searchTerm })
        });

        const result = await response.json();

        if (response.ok) {
            console.log("Transcript search successful:", result);
            sendResponse({ status: "success", data: result });
        } else {
            throw new Error(result.message || "Transcript search failed.");
        }
    } catch (error) {
        console.error("Transcript search error:", error);
        sendResponse({ status: "error", message: error.message });
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

    try {
        const apiUrl = `http://localhost:5000${endpoint}`;
        const requestBody = { ...payload, videoId: finalVideoId };  // Auto-add videoId if not in payload

        const response = await fetch(apiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
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

/**
 * Optional: Validates the schema of the object search response.
 */
function validateObjectSearchResponse(data) {
    // Example schema validation
    return (
        Array.isArray(data.results) &&
        data.results.every(item =>
            typeof item.timestamp === 'string' &&
            typeof item.confidence === 'number'
        )
    );
}
