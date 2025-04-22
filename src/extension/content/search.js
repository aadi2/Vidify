document.addEventListener("DOMContentLoaded", function() {
    const searchButton = document.getElementById("search-button");
    const searchInput = document.getElementById("search-input");
    const resultsContainer = document.getElementById("results-container");
    const statusMessage = document.getElementById("status-message");
    const loadingSpinner = document.getElementById("loading-spinner");
    const searchModeToggle = document.getElementById("search-mode-toggle");
    const modeLabel = document.getElementById("mode-label");
    const darkModeToggle = document.getElementById("dark-mode-toggle");
    
    // Store event listeners for proper cleanup
    const eventListeners = [];

    // Debounce function to limit API requests
    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            const context = this;
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(context, args), wait);
        };
    }

    // Initialize UI
    statusMessage.classList.remove("hidden");
    statusMessage.textContent = "Welcome to Vidify! Please search using a keyword...";

    // Dark mode toggle handler
    const handleDarkModeToggle = function() {
        document.body.classList.toggle("dark-mode", darkModeToggle.checked);
    };
    darkModeToggle.addEventListener("change", handleDarkModeToggle);
    eventListeners.push({ element: darkModeToggle, type: 'change', handler: handleDarkModeToggle });

    // Search mode toggle handler
    const handleSearchModeToggle = function() {
        modeLabel.textContent = searchModeToggle.checked ? "Object Detection" : "Transcript Search";
    };
    searchModeToggle.addEventListener("change", handleSearchModeToggle);
    eventListeners.push({ element: searchModeToggle, type: 'change', handler: handleSearchModeToggle });

    // Progress bar updates
    function updateProgressBar(value) {
        document.getElementById("progress-bar").style.width = value + "%";
    }

    // Extract video ID from URL
    function extractVideoId(url) {
        const match = url.match(/[?&]v=([^&]+)/);
        return match ? match[1] : null;
    }

    // Get active tab URL
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

    // Display results in popup
    function displayResultsInPopup(data) {
        // Clear previous results
        while (resultsContainer.firstChild) {
            resultsContainer.removeChild(resultsContainer.firstChild);
        }
        
        // Create document fragment for better performance
        const fragment = document.createDocumentFragment();
        
        const heading = document.createElement("h3");
        heading.textContent = "Results:";
        fragment.appendChild(heading);
    
        if (!data.results || data.results.length === 0) {
            const noResults = document.createElement("p");
            noResults.textContent = "No results found.";
            fragment.appendChild(noResults);
            resultsContainer.appendChild(fragment);
            return;
        }
    
        // Process results in batches for better performance with large datasets
        const processResultsBatch = (results, startIndex, batchSize) => {
            const endIndex = Math.min(startIndex + batchSize, results.length);
            
            for (let i = startIndex; i < endIndex; i++) {
                const result = results[i];
                const item = document.createElement("div");
                item.className = "result-item";
                
                // Highlight keyword more efficiently
                const searchTerm = searchInput.value.trim();
                const text = result.text || "";
                
                // Use regular expression once per item instead of creating regex in loop
                let highlightedText = text.replace(
                    new RegExp(searchTerm, "gi"),
                    match => `<span class="result-highlight">${match}</span>`
                );
                
                item.innerHTML = `${highlightedText} at <strong>${result.timestamp}s</strong>`;
                fragment.appendChild(item);
            }
            
            // Process next batch or append to DOM
            if (endIndex < results.length) {
                setTimeout(() => {
                    processResultsBatch(results, endIndex, batchSize);
                }, 0);
            } else {
                resultsContainer.appendChild(fragment);
            }
        };
        
        // Start processing with first batch of 20 items
        processResultsBatch(data.results, 0, 20);
    }

    // Perform search with debounce
    const performSearch = debounce(async function() {
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
            updateProgressBar(10); // Move to 10% after a moment
        }, 200);
        
        // Clear previous results
        while (resultsContainer.firstChild) {
            resultsContainer.removeChild(resultsContainer.firstChild);
        }

        const videoId = await getActiveTabUrl();
        console.log("Extracted Video URL:", videoId);

        if (!videoId) {
            alert("Could not detect a video ID. Please make sure you're on a YouTube video page.");
            // Hide loading UI
            loadingSpinner.classList.remove("rotating");
            loadingSpinner.style.display = "none";
            document.querySelector(".progress-container").style.display = "none";
            return;
        }
        
        // Update progress
        setTimeout(() => {
            updateProgressBar(60);
        }, 500);
        
        try {
            const response = await chrome.runtime.sendMessage({
                action: searchModeToggle.checked ? "searchObjects" : "searchTranscript",
                videoId: videoId,
                searchTerm: query
            });
            
            updateProgressBar(100); 
            setTimeout(() => {
                document.querySelector(".progress-container").style.display = "none";
            }, 200);

            loadingSpinner.classList.remove("rotating"); 
            loadingSpinner.style.display = "none"; 

            if (response && response.status === 'success' && response.data) {
                statusMessage.textContent = "Search complete!";
                displayResultsInPopup(response.data);
            } else {
                statusMessage.textContent = "No results found.";
            }

        } catch (error) {
            console.error('Error during search:', error);
            const errorMsg = document.createElement("p");
            errorMsg.style.color = "red";
            errorMsg.textContent = `Search failed: ${error.message || "Unknown error"}`;
            resultsContainer.appendChild(errorMsg);
            
            // Hide loading UI
            loadingSpinner.classList.remove("rotating");
            loadingSpinner.style.display = "none";
            document.querySelector(".progress-container").style.display = "none";
        }
    }, 300); // 300ms debounce

    // Search button handler
    const handleSearch = function() {
        performSearch();
    };
    searchButton.addEventListener("click", handleSearch);
    eventListeners.push({ element: searchButton, type: 'click', handler: handleSearch });
    
    // Keyboard handler for search input
    const handleKeyDown = function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    };
    searchInput.addEventListener("keydown", handleKeyDown);
    eventListeners.push({ element: searchInput, type: 'keydown', handler: handleKeyDown });

    // Cleanup function to remove event listeners when popup closes
    function cleanup() {
        eventListeners.forEach(({ element, type, handler }) => {
            if (element) {
                element.removeEventListener(type, handler);
            }
        });
    }
    
    // Handle popup close
    window.addEventListener('unload', cleanup);
});

// Move outside the DOMContentLoaded handler since it doesn't depend on the DOM
function extractVideoId(url) {
    const match = url.match(/[?&]v=([^&]+)/);
    return match ? match[1] : null;
}

function updateProgressBar(value) {
    const progressBar = document.getElementById("progress-bar");
    if (progressBar) {
        progressBar.style.width = value + "%";
    }
}