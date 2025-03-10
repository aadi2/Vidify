document.addEventListener("DOMContentLoaded", function() {
    const searchButton = document.getElementById("search-button");
    const searchInput = document.getElementById("search-input");
    const resultsContainer = document.getElementById("results-container");

    searchButton.addEventListener("click", async function() {
        const query = searchInput.value.trim();
        
        if (query === "") {
            alert("Please enter a search term.");
            return;
        }

        // Attempt to extract videoId from the current tab's URL
      // NOTE: Because this is the popup, we need to query the active tab:
      
        // Placeholder for search logic
        resultsContainer.innerHTML = `<p>Searching for "${query}" in the video...</p>`;
        // Send message to background.js to perform object search (you could change this to support transcript search too)
        const videoId = await getActiveTabUrl();
        console.log("Extracted Video URL:", videoId);

        if (!videoId) {
            alert("Could not detect a video ID. Please make sure you're on a YouTube video page.");
            return;
        }
        try {
            const response = await chrome.runtime.sendMessage({
                action: "searchTranscript",
                videoId: videoId,
                searchTerm: query
            });
            if (response && response.status === 'success' && response.data) {
                displayResultsInPopup(response.data);
                //sendResultsToContentScript(response.data.results);
            } else {
                resultsContainer.innerHTML = `<p style="color: red;">Search failed: ${response || "Unknown error"}</p>`;
            }
            console.log(response);
        
        } catch (error) {
            console.error('Error during search:', error);
            resultsContainer.innerHTML = `<p style="color: red;">Search failed: ${error.message || "Unknown error"}</p>`;
        }
    });

    async function getActiveTabUrl() {
        return new Promise((resolve, reject) => {
            chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                if (chrome.runtime.lastError) {
                    return reject(new Error(chrome.runtime.lastError));
                }
                if (!tabs || tabs.length === 0) {
                    return reject(new Error("No active tab found."));
                }
    
                const videoId = extractVideoId(tabs[0].url);
                resolve(videoId);
            });
        });
    }

    function displayResultsInPopup(data) {
        //const resultsContainer = document.getElementById("results-container");
        resultsContainer.innerHTML = "<h3>Search Results:</h3>";
    
        if (!data.results || data.results.length === 0) {
            resultsContainer.innerHTML += `<p>No results found.</p>`;
            return;
        }
    
        data.results.forEach(result => {
            const item = document.createElement("p");
            item.textContent = `${result.text} at ${result.timestamp}s`;
            resultsContainer.appendChild(item);
        });
    }

});



/**
 * Extract YouTube video ID from URL.
 * This works both in popup context and content script context.
 */
function extractVideoId(url) {
    const match = url.match(/[?&]v=([^&]+)/);
    return match ? match[1] : null;
}

/**
 * Display search results directly inside the popup.
 * @param {Object} data - Response data containing search results.
 */
function displayResultsInPopup(data) {
    const resultsContainer = document.getElementById("results-container");
    resultsContainer.innerHTML = "<h3>Search Results:</h3>";

    if (!data.results || data.results.length === 0) {
        resultsContainer.innerHTML += `<p>No results found.</p>`;
        return;
    }

    data.results.forEach(result => {
        const item = document.createElement("p");
        item.textContent = `Object: ${result.object} at ${result.timestamp}s`;
        resultsContainer.appendChild(item);
    });
}

/**
 * Send results to content.js so they appear as an overlay on the video.
 */
function sendResultsToContentScript(results) {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs.length > 0) {
            chrome.tabs.sendMessage(tabs[0].id, {
                action: "displayResults",
                data: results
            });
        }
    });
}
