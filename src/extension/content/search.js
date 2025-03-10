document.addEventListener("DOMContentLoaded", function() {
    const searchButton = document.getElementById("search-button");
    const searchInput = document.getElementById("search-input");
    const resultsContainer = document.getElementById("results-container");
    const statusMessage = document.getElementById("status-message");
    const loadingSpinner = document.getElementById("loading-spinner");

    statusMessage.classList.remove("hidden");
    statusMessage.textContent = "Welcome to Vidify! Please search for an item in this video.";

    searchButton.addEventListener("click", async function() {
        const query = searchInput.value.trim();
        
        if (query === "") {
            alert("Please enter a search term.");
            return;
        }

        resultsContainer.innerHTML = `<p>Searching for "${query}" in the video...</p>`;
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

function extractVideoId(url) {
    const match = url.match(/[?&]v=([^&]+)/);
    return match ? match[1] : null;
}
