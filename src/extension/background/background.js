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
chrome.runtime.onMessage.addListener(async (request, sender, sendResponse) => {
    try {
        switch (request.action) {
            //case "searchObject":
                //await handleObjectSearch(request.videoId, request.objectName, sendResponse);
                //break;

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
*/

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
        sendResponse({ status: "success", data: result });
      } else {
        throw new Error(result.message || `Transcript search failed with status ${response.status} ${response.statusText}`);
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
*/