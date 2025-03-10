document.addEventListener("DOMContentLoaded", function() {
    const searchButton = document.getElementById("search-button");
    const searchInput = document.getElementById("search-input");
    const resultsContainer = document.getElementById("results-container");
    const statusMessage = document.getElementById("status-message");
    const loadingSpinner = document.getElementById("loading-spinner");
    const searchModeToggle = document.getElementById("search-mode-toggle");
    const modeLabel = document.getElementById("mode-label");
    const darkModeToggle = document.getElementById("dark-mode-toggle")


    statusMessage.classList.remove("hidden");
    statusMessage.textContent = "Welcome to Vidify! Start searching...";

    searchButton.addEventListener("click", async function() {
        const query = searchInput.value.trim();
    
        if (query === "") {
            alert("Please enter a search term.");
            return;
        }

        // Placeholder for search logic
        resultsContainer.innerHTML = `<p>Searching for "${query}" in the video...</p>`;

        loadingSpinner.style.display = "block";

        // Send message to background.js to perform object search (you could change this to support transcript search too)
        const videoId = await getActiveTabUrl();
        if (!videoId) {
            alert("Could not detect a video ID. Please make sure you're on a YouTube video page.");
            loadingSpinner.style.display = "none";
            return;
        }
        try {
            const response = await chrome.runtime.sendMessage({
                action: searchModeToggle.checked ? "searchObjects" : "searchTranscript",
                videoId: videoId,
                searchTerm: query
            });
            loadingSpinner.style.display = "none";

            if (response && response.status === 'success' && response.data) {
                displayResultsInPopup(response.data);
            } else {
                resultsContainer.innerHTML = `<p style="color: red;">Search failed: ${response || "Unknown error"}</p>`;
            }
            console.log(response);
        } catch (error) {
            console.error('Error during search:', error);
            resultsContainer.innerHTML = `<p style="color: red;">Search failed: ${error.message || "Unknown error"}</p>`;
        }
    });

    searchModeToggle.addEventListener("change", function() {
        modeLabel.textContent = searchModeToggle.checked ? "Object Detection" : "Transcript Search";
    });

    darkModeToggle.addEventListener("change", function() {
        document.body.classList.toggle("dark-mode", darkModeToggle.checked);
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
