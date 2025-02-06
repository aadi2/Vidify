// When the extension is installed or updated
chrome.runtime.onInstalled.addListener(() => {
    console.log("Vidify extension installed and ready!");
});

/**
 * Listen for messages from content scripts or the extension popup
 * Handles requests such as object detection, transcript search, and search history
 */
chrome.runtime.onMessage.addListener(async (request, sender, sendResponse) => {
    try {
        switch (request.action) {
            case "searchObject":
                await handleObjectSearch(request.videoId, request.objectName, sendResponse);
                break;

            case "searchTranscript":
                await handleTranscriptSearch(request.videoId, request.searchTerm, sendResponse);
                break;

            case "getSearchHistory":
                handleSearchHistory(sendResponse);
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
 * Handles object detection search by making an API call to the backend.
 * @param {string} videoId - YouTube video ID
 * @param {string} objectName - Name of the object to search for
 * @param {function} sendResponse - Function to send response back to the caller
 */
async function handleObjectSearch(videoId, objectName, sendResponse) {
    try {
        console.log(`Searching for object: ${objectName} in video: ${videoId}`);
        
        // Example API endpoint (modify according to your backend setup)
        const apiUrl = `http://localhost:5000/search/object`;

        const response = await fetch(apiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ videoId, objectName })
        });

        const result = await response.json();

        if (response.ok) {
            console.log("Object detection successful:", result);
            sendResponse({ status: "success", data: result });
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
    try {
        console.log(`Searching for term: ${searchTerm} in video: ${videoId}`);

        // Example API endpoint (modify according to your backend setup)
        const apiUrl = `http://localhost:5000/search/transcript`;

        const response = await fetch(apiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ videoId, searchTerm })
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
