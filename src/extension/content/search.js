document.addEventListener("DOMContentLoaded", function() {
    const searchButton = document.getElementById("search-button");
    const searchInput = document.getElementById("search-input");
    const resultsContainer = document.getElementById("results-container");
    const statusMessage = document.getElementById("status-message");
    const loadingSpinner = document.getElementById("loading-spinner");
    const searchModeToggle = document.getElementById("search-mode-toggle");
    const modeLabel = document.getElementById("mode-label");
    const darkModeToggle = document.getElementById("dark-mode-toggle");


    statusMessage.classList.remove("hidden");
    statusMessage.textContent = "Welcome to Vidify! Please search for an item in this video.";

    darkModeToggle.addEventListener("change", function() {
        document.body.classList.toggle("dark-mode", darkModeToggle.checked);
    });

    searchModeToggle.addEventListener("change", function() {
        modeLabel.textContent = searchModeToggle.checked ? "Object Detection" : "Transcript Search";
    });

    searchButton.addEventListener("click", async function() {
        const query = searchInput.value.trim();
        
        if (query === "") {
            alert("Please enter a search term.");
            return;
        }

        statusMessage.textContent = `Searching for "${query}"...`;
        loadingSpinner.style.display = "block";
        document.querySelector(".progress-container").style.display = "block"; 
        updateProgressBar(0);
        setTimeout(() => {
            updateProgressBar(10); // Move to 100% after 1.5 seconds
        }, 1500);
        resultsContainer.innerHTML = ""; 

        const videoId = await getActiveTabUrl();
        console.log("Extracted Video URL:", videoId);

        if (!videoId) {
            alert("Could not detect a video ID. Please make sure you're on a YouTube video page.");
            return;
        }
        try {
            const response = await chrome.runtime.sendMessage({
                action: searchModeToggle.checked ? "searchObjects" : "searchTranscript",
                videoId: videoId,
                searchTerm: query
            });
            
            updateProgressBar(60); // Move to 60% after search completes
            updateProgressBar(100); // Move to 100% after 1.5 seconds
            setTimeout(() => {
                document.querySelector(".progress-container").style.display = "none"; // Hide bar
            }, 500);

            loadingSpinner.style.display = "none"; // Hide spinner after search

            if (response && response.status === 'success' && response.data) {
                statusMessage.textContent = "Search complete!";
                displayResultsInPopup(response.data);
            } else {
                statusMessage.textContent = "No results found.";
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
        resultsContainer.innerHTML = "<h3>Results:</h3>";
    
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

function updateProgressBar(value) {
    document.getElementById("progress-bar").style.width = value + "%";
}