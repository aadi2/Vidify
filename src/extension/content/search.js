document.addEventListener("DOMContentLoaded", function() {
    const searchButton = document.getElementById("search-button");
    const searchInput = document.getElementById("search-input");
    const resultsContainer = document.getElementById("results-container");
    const statusMessage = document.getElementById("status-message");
    const loadingSpinner = document.getElementById("loading-spinner");
    const searchModeToggle = document.getElementById("search-mode-toggle");
    const modeLabel = document.getElementById("mode-label");
    const darkModeToggle = document.getElementById("dark-mode-toggle");

    // Track if we're in popup or sidebar mode
    const isPopup = window.location.href.includes('popup');

    statusMessage.classList.remove("hidden");
    statusMessage.textContent = "Welcome to Vidify! Please search using a keyword...";

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

        loadingSpinner.style.display = "flex"; 
        loadingSpinner.classList.add("rotating");

        document.querySelector(".progress-container").style.display = "block"; 
        updateProgressBar(0);
        setTimeout(() => {
            updateProgressBar(10); // Move to 10% after 1.5 seconds
        }, 1500);
        resultsContainer.innerHTML = ""; 

        const tabInfo = await getActiveTab();
        console.log("Active tab info:", tabInfo);

        if (!tabInfo.videoId) {
            alert("Could not detect a video ID. Please make sure you're on a YouTube video page.");
            return;
        }
        setTimeout(() => {
            updateProgressBar(60); // Move to 60% after 5 seconds
        }, 5000);
        try {
            const response = await chrome.runtime.sendMessage({
                action: searchModeToggle.checked ? "searchObjects" : "searchTranscript",
                videoId: tabInfo.videoId,
                searchTerm: query
            });
            
            updateProgressBar(100); 
            setTimeout(() => {
                document.querySelector(".progress-container").style.display = "none"; // Hide bar
            }, 500);

            loadingSpinner.classList.remove("rotating"); 
            loadingSpinner.style.display = "none"; 

            if (response && response.status === 'success' && response.data) {
                statusMessage.textContent = "Search complete!";
                displayResultsInPopup(response.data, tabInfo);
            } else {
                statusMessage.textContent = "No results found.";
            }

            console.log(response);

        } catch (error) {
            console.error('Error during search:', error);
            resultsContainer.innerHTML = `<p style="color: red;">Search failed: ${error.message || "Unknown error"}</p>`;
        }
    });

    async function getActiveTab() {
        return new Promise((resolve, reject) => {
            chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                if (!tabs || tabs.length === 0) {
                    return reject(new Error("No active tab found."));
                }
                
                const tab = tabs[0];
                const videoId = extractVideoId(tab.url);
                
                resolve({
                    tabId: tab.id,
                    url: tab.url,
                    videoId: videoId
                });
            });
        });
    }

    function displayResultsInPopup(data, tabInfo) {
        resultsContainer.innerHTML = `<h3>Results:</h3>`;
    
        if (!data.results || data.results.length === 0) {
            resultsContainer.innerHTML += `<p>No results found.</p>`;
            return;
        }
    
        data.results.forEach(result => {
            const item = document.createElement("div");
            item.className = "result-item";
    
            // Highlight keyword in text
            let text = result.text;
            if (searchInput.value.trim()) {
                const regex = new RegExp(`(${searchInput.value.trim()})`, 'gi');
                text = text.replace(regex, '<span class="result-highlight">$1</span>');
            }
    
            // Parse the timestamp to seconds (critical for correct navigation)
            const seconds = parseTimestamp(result.timestamp);
            
            // Create timestamp button instead of a link
            const timeButton = document.createElement("button");
            timeButton.className = "clickable-timestamp";
            timeButton.textContent = result.timestamp;
            timeButton.setAttribute("data-seconds", seconds);
            timeButton.addEventListener("click", function() {
                const exactSeconds = this.getAttribute("data-seconds");
                console.log(`Navigating to ${exactSeconds} seconds`);
                
                // Create the YouTube URL with timestamp
                // Use the explicit format that YouTube requires
                const youtubeUrl = `https://www.youtube.com/watch?v=${tabInfo.videoId}&t=${Math.floor(exactSeconds)}s`;
                console.log("Navigation URL:", youtubeUrl);
                
                // Navigate directly to the URL
                chrome.tabs.update(tabInfo.tabId, {
                    url: youtubeUrl
                });
                
                // If in popup mode, close the popup after a short delay
                if (isPopup) {
                    setTimeout(() => window.close(), 300);
                }
            });
    
            // Build result item
            item.innerHTML = `${text} at `;
            item.appendChild(timeButton);
            
            resultsContainer.appendChild(item);
        });
    }

    // Helper function to parse timestamps to seconds - this MUST be accurate
    function parseTimestamp(timestamp) {
        console.log("Parsing timestamp:", timestamp);
        
        // Remove 's' suffix if present
        timestamp = timestamp.toString().replace(/s$/, '');
        
        // Try parsing as a simple float first
        let seconds = parseFloat(timestamp);
        if (!isNaN(seconds)) {
            console.log("Parsed as float:", seconds);
            return seconds;
        }
        
        // Parse timestamp in format "00:01:23.456"
        const match = timestamp.match(/^(?:(\d+):)?(\d+):(\d+)(?:\.(\d+))?$/);
        if (match) {
            const hours = match[1] ? parseInt(match[1], 10) : 0;
            const minutes = parseInt(match[2], 10);
            const seconds = parseInt(match[3], 10);
            const milliseconds = match[4] ? parseInt(match[4], 10) / Math.pow(10, match[4].length) : 0;
            
            const totalSeconds = hours * 3600 + minutes * 60 + seconds + milliseconds;
            console.log("Parsed from time format:", totalSeconds);
            return totalSeconds;
        }
        
        // If all else fails, return 0
        console.error(`Failed to parse timestamp: ${timestamp}`);
        return 0;
    }
});

function extractVideoId(url) {
    if (!url) return null;
    
    // Handle regular YouTube URL
    let match = url.match(/[?&]v=([^&]+)/);
    if (match) return match[1];
    
    // Handle shortened youtu.be URL
    match = url.match(/youtu\.be\/([^?]+)/);
    if (match) return match[1];
    
    return null;
}

function updateProgressBar(value) {
    document.getElementById("progress-bar").style.width = value + "%";
}