document.addEventListener("DOMContentLoaded", function() {
    const searchButton = document.getElementById("search-button");
    const searchInput = document.getElementById("search-input");
    const resultsContainer = document.getElementById("results-container");
    const statusMessage = document.getElementById("status-message");
    const loadingSpinner = document.getElementById("loading-spinner");
    const searchModeToggle = document.getElementById("search-mode-toggle");
    const modeLabel = document.getElementById("mode-label");
    const darkModeToggle = document.getElementById("dark-mode-toggle");

    const tocContainer = document.createElement("div");
    tocContainer.id = "toc-container";
    tocContainer.style.marginTop = "10px";
    tocContainer.classList.add("hidden");
    document.body.appendChild(tocContainer);

    statusMessage.classList.remove("hidden");
    statusMessage.textContent = "Welcome to Vidify! Please search using a keyword...";

    darkModeToggle.addEventListener("change", function() {
        document.body.classList.toggle("dark-mode", darkModeToggle.checked);
    });

    searchModeToggle.addEventListener("change", function() {
        const isObjectDetection = searchModeToggle.checked;
        modeLabel.textContent = isObjectDetection ? "Object Detection" : "Transcript Search";

        if (isObjectDetection) {
            searchInput.classList.add("hidden");
            searchButton.classList.add("hidden");
            resultsContainer.classList.add("hidden");
            tocContainer.classList.remove("hidden");
            statusMessage.textContent = "Fetching object detection TOC...";
            fetchObjectTOC();
        } else {
            searchInput.classList.remove("hidden");
            searchButton.classList.remove("hidden");
            resultsContainer.classList.remove("hidden");
            tocContainer.classList.add("hidden");
            statusMessage.textContent = "Welcome to Vidify! Please search using a keyword...";
        }
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
            updateProgressBar(10);
        }, 1500);
        resultsContainer.innerHTML = "";

        const videoId = await getActiveTabUrl();
        console.log("Extracted Video URL:", videoId);

        if (!videoId) {
            alert("Could not detect a video ID. Please make sure you're on a YouTube video page.");
            return;
        }

        setTimeout(() => {
            updateProgressBar(60);
        }, 5000);

        try {
            const response = await chrome.runtime.sendMessage({
                action: searchModeToggle.checked ? "searchObjects" : "searchTranscript",
                videoId: videoId,
                searchTerm: query
            });

            updateProgressBar(100);
            setTimeout(() => {
                document.querySelector(".progress-container").style.display = "none";
            }, 500);

            loadingSpinner.classList.remove("rotating");
            loadingSpinner.style.display = "none";

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
        resultsContainer.innerHTML = `<h3>Results:</h3>`;

        if (!data.results || data.results.length === 0) {
            resultsContainer.innerHTML += `<p>No results found.</p>`;
            return;
        }

        data.results.forEach(result => {
            const item = document.createElement("div");
            item.className = "result-item";

            let highlightedText = result.text.replace(
                new RegExp(searchInput.value, "gi"),
                (match) => `<span class="result-highlight">${match}</span>`
            );

            item.innerHTML = `${highlightedText} at <strong>${result.timestamp}s</strong>`;
            resultsContainer.appendChild(item);
        });
    }

    async function fetchObjectTOC() {
        const ytUrl = window.location.href;
        try {
            const response = await fetch(`http://127.0.0.1:8001/object_search?yt_url=${encodeURIComponent(ytUrl)}`);
            const data = await response.json();

            if (response.ok && data.results) {
                renderTOC(data.results);
                statusMessage.textContent = "Objects fetched successfully.";
            } else {
                tocContainer.innerHTML = `<p>${data.message || "Error fetching TOC"}</p>`;
            }
        } catch (error) {
            tocContainer.innerHTML = `<p>Failed to fetch objects: ${error.message}</p>`;
        }
    }

    function renderTOC(data) {
        tocContainer.innerHTML = "";

        if (!Object.keys(data).length) {
            tocContainer.innerHTML = "<p>No objects detected.</p>";
            return;
        }

        for (const [objectName, timestamps] of Object.entries(data)) {
            const section = document.createElement("div");
            section.className = "toc-object";
            section.innerHTML = `<h3>${objectName}</h3>`;

            const list = document.createElement("ul");
            timestamps.forEach(ts => {
                const li = document.createElement("li");
                li.textContent = `${ts.toFixed(2)}s`;
                li.style.cursor = "pointer";
                li.onclick = () => {
                    const video = document.querySelector("video");
                    if (video) video.currentTime = ts;
                };
                list.appendChild(li);
            });

            section.appendChild(list);
            tocContainer.appendChild(section);
        }
    }
});

function extractVideoId(url) {
    const match = url.match(/[?&]v=([^&]+)/);
    return match ? match[1] : null;
}

function updateProgressBar(value) {
    document.getElementById("progress-bar").style.width = value + "%";
}