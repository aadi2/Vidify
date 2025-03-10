document.addEventListener("DOMContentLoaded", function() {
    const searchButton = document.getElementById("search-button");
    const searchInput = document.getElementById("search-input");
    const resultsContainer = document.getElementById("results-container");
    const statusMessage = document.getElementById("status-message");
    const loadingSpinner = document.getElementById("loading-spinner");


    statusMessage.classList.remove("hidden");
    statusMessage.textContent = "Welcome to Vidify! Please search for an item in this video.";

    searchButton.addEventListener("click", function() {
        const query = searchInput.value.trim();
        
        if (query === "") {
            alert("Please enter a search term.");
            return;
        }

        const videoId = extractVideoId(window.location.href);

        if (!videoId) {
            alert("Could not detect a video ID. Please make sure you're on a YouTube video page.");
            return;
        }

        // Placeholder for search logic
        resultsContainer.innerHTML = `<p>Searching for "${query}" in the video...</p>`;

        // Send message to background.js to perform object search (you could change this to support transcript search too)
        chrome.runtime.sendMessage({
            action: "searchObject",
            videoId: videoId,
            objectName: query
        }, (response) => {

            loadingSpinner.style.display = "none"; // Hide spinner after processing

            if (response && response.status === "success") {
                statusMessage.textContent = "Search completed! Results displayed below.";
                displayResultsInPopup(response.data);
                sendResultsToContentScript(response.data.results);
            } else {
                resultsContainer.innerHTML = `<p style="color: red;">Search failed: ${response?.message || "Unknown error"}</p>`;
            }
        });
    });



    // This works both in popup context and content script context.
    function extractVideoId(url) {
        const match = url.match(/[?&]v=([^&]+)/);
        return match ? match[1] : null;
    }

    /**
     * Display search results directly inside the popup.
     * @param {Object} data - Response data containing search results.
     */
    function displayResultsInPopup(data) {
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

    // Send results to content.js so they appear as an overlay on the video.
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
});
