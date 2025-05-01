document.addEventListener("DOMContentLoaded", function() {
    const searchButton = document.getElementById("search-button");
    const searchInput = document.getElementById("search-input");
    
    searchInput.addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
            event.preventDefault();  // Prevent form submission if inside a form
            searchButton.click();    // Trigger the search
        }
    });
    
    const resultsContainer = document.getElementById("results-container");
    const statusMessage = document.getElementById("status-message");
    const loadingSpinner = document.getElementById("loading-spinner");
    const searchModeToggle = document.getElementById("search-mode-toggle");
    const modeLabel = document.getElementById("mode-label");
    const darkModeToggle = document.getElementById("dark-mode-toggle");


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

        const videoId = await getActiveTabUrl();
        console.log("Extracted Video URL:", videoId);

        if (!videoId) {
            alert("Could not detect a video ID. Please make sure you're on a YouTube video page.");
            return;
        }
        setTimeout(() => {
            updateProgressBar(60); // Move to 10% after 1.5 seconds
        }, 5000);
        try {
            const response = await chrome.runtime.sendMessage({
                action: searchModeToggle.checked ? "searchObjects" : "searchTranscript",
                videoId: videoId,
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
                displayResultsInPopup(response.data, videoId);
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
                resolve(tabs[0].url);
            });
        });
    }

    function displayResultsInPopup(data, videoId) {
        resultsContainer.innerHTML = `<h3>Results:</h3>`;
    
        if (!data.results || data.results.length === 0) {
            resultsContainer.innerHTML += `<p>No results found.</p>`;
            return;
        }
    
        data.results.forEach(result => {
            const item = document.createElement("div");
            item.className = "result-item";
    
            // Highlight keyword
            let highlightedText = result.text.replace(
                new RegExp(searchInput.value, "gi"),
                (match) => `<span class="result-highlight">${match}</span>`
            );
    
            const seconds = typeof result.timestamp === "string" && result.timestamp.includes(":")
                ? parseTimestampToSeconds(result.timestamp)
                : result.timestamp;

            const link = `https://www.youtube.com/watch?v=${videoId}&t=${Math.floor(seconds)}s`;

            item.innerHTML = `${highlightedText} at `;

            // Create clickable timestamp
            const timestampSpan = document.createElement("span");
            timestampSpan.textContent = `${result.timestamp}s`;
            timestampSpan.className = "timestamp-link";
            timestampSpan.style.color = "#007bff";
            timestampSpan.style.cursor = "pointer";
            timestampSpan.style.textDecoration = "underline";
            timestampSpan.setAttribute("data-seconds", seconds);
            
            // Send message to content script to seek
            timestampSpan.addEventListener("click", () => {
                chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                    chrome.scripting.executeScript({
                        target: { tabId: tabs[0].id },
                        func: (seekTime) => {
                            const video = document.querySelector("video");
                            if (video) {
                                video.currentTime = seekTime;
                                video.play();
                            }
                        },
                        args: [seconds]
                    });
                });
                
            });
            
            item.appendChild(timestampSpan);
            
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

function parseTimestampToSeconds(ts) {
    const parts = ts.replace("s", "").split(":").map(parseFloat);
    if (parts.length === 3) {
        const [hours, minutes, seconds] = parts;
        return hours * 3600 + minutes * 60 + seconds;
    } else if (parts.length === 2) {
        const [minutes, seconds] = parts;
        return minutes * 60 + seconds;
    }
    return parseFloat(ts);
}