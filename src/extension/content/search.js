document.addEventListener("DOMContentLoaded", function () {
    const searchButton = document.getElementById("search-button");
    const searchInput = document.getElementById("search-input");

    searchInput.addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
            event.preventDefault();
            searchButton.click();
        }
    });

    const resultsContainer = document.getElementById("results-container");
    const statusMessage = document.getElementById("status-message");
    const loadingSpinner = document.getElementById("loading-spinner");
    const searchModeToggle = document.getElementById("search-mode-toggle");
    const modeLabel = document.getElementById("mode-label");
    const darkModeToggle = document.getElementById("dark-mode-toggle");
    let cachedTOC = null;

    statusMessage.classList.remove("hidden");
    statusMessage.textContent = "Welcome to Vidify! Please search using a keyword...";

    darkModeToggle.addEventListener("change", function () {
        document.body.classList.toggle("dark-mode", darkModeToggle.checked);
    });

    searchModeToggle.addEventListener("change", async function () {
        modeLabel.textContent = searchModeToggle.checked ? "Object Detection" : "Transcript Search";

        resultsContainer.innerHTML = "";
        const query = searchInput.value.trim();

        if (searchModeToggle.checked && query === "") {
            statusMessage.textContent = "Loading detected objects...";
            const videoId = await getActiveTabUrl();
            loadObjectTOC(videoId);
        } else {
            statusMessage.textContent = "Welcome to Vidify! Please search using a keyword...";
        }
    });

    searchButton.addEventListener("click", async function () {
        const query = searchInput.value.trim();
        if (query === "") {
            alert("Please enter a search term.");
            return;
        }

        statusMessage.textContent = `Searching for "${query}"...`;
        loadingSpinner.style.display = "flex";
        loadingSpinner.classList.add("rotating");
        resultsContainer.innerHTML = "";

        const videoId = await getActiveTabUrl();
        if (!videoId) {
            alert("Could not detect a video ID. Please make sure you're on a YouTube video page.");
            return;
        }

        try {
            const response = await chrome.runtime.sendMessage({
                action: searchModeToggle.checked ? "searchObjects" : "searchTranscript",
                videoId: videoId,
                searchTerm: query,
            });

            loadingSpinner.classList.remove("rotating");
            loadingSpinner.style.display = "none";

            if (response && response.status === "success" && response.data) {
                statusMessage.textContent = "Search complete!";
                displayResultsInPopup(response.data, videoId);
            } else {
                statusMessage.textContent = "No results found.";
            }
        } catch (error) {
            console.error("Error during search:", error);
            resultsContainer.innerHTML = `<p style="color: red;">Search failed: ${error.message || "Unknown error"}</p>`;
        }
    });

    if (searchModeToggle.checked) {
        getActiveTabUrl().then((videoId) => {
            loadObjectTOC(videoId);
        });
    }

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

        data.results.forEach((result) => {
            const label = result.text || result.object || "Result";

            if (result.timestamps !== undefined) {
                const timestamps = Array.isArray(result.timestamps) ? result.timestamps : [result.timestamps];

                timestamps.forEach((ts) => {
                    const seconds = typeof ts === "string" ? parseTimestampToSeconds(ts) : ts;

                    const item = document.createElement("div");
                    item.className = "result-item";
                    item.innerHTML = `<strong>${label}</strong> at `;

                    const timestampSpan = document.createElement("span");
                    timestampSpan.textContent = `${seconds.toFixed(1)}s`;
                    timestampSpan.className = "timestamp-link";
                    timestampSpan.style.color = "#007bff";
                    timestampSpan.style.cursor = "pointer";
                    timestampSpan.style.textDecoration = "underline";
                    timestampSpan.setAttribute("data-seconds", seconds);

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
                                args: [seconds],
                            });
                        });
                    });

                    item.appendChild(timestampSpan);
                    resultsContainer.appendChild(item);
                });
            } else if (result.timestamp !== undefined) {
                const seconds = typeof result.timestamp === "string" ? parseTimestampToSeconds(result.timestamp) : result.timestamp;

                const item = document.createElement("div");
                item.className = "result-item";
                item.innerHTML = `<strong>${label}</strong> at `;

                const timestampSpan = document.createElement("span");
                timestampSpan.textContent = `${seconds.toFixed(1)}s`;
                timestampSpan.className = "timestamp-link";
                timestampSpan.style.color = "#007bff";
                timestampSpan.style.cursor = "pointer";
                timestampSpan.style.textDecoration = "underline";
                timestampSpan.setAttribute("data-seconds", seconds);

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
                            args: [seconds],
                        });
                    });
                });

                item.appendChild(timestampSpan);
                resultsContainer.appendChild(item);
            }
        });
    }

    function loadObjectTOC(videoId) {
        if (!videoId) return;

        chrome.runtime.sendMessage({
            action: "tableOfContents",
            videoId: videoId,
        }, (response) => {
            if (response && response.status === "success" && response.data) {
                cachedTOC = response.data;
                renderTOC(cachedTOC, videoId);
            } else {
                resultsContainer.innerHTML = "<p>Failed to load detected objects.</p>";
            }
        });
    }

    function renderTOC(tocData, videoId) {
        resultsContainer.innerHTML = "<h3>Detected Objects:</h3>";

        const list = document.createElement("ul");
        tocData.results.forEach((obj) => {
            const listItem = document.createElement("li");
            listItem.textContent = obj.object;
            listItem.style.cursor = "pointer";
            listItem.style.color = "#007bff";
            listItem.style.textDecoration = "underline";

            listItem.onclick = () => {
                renderTimestamps(obj.object, obj.timestamps, videoId);
            };

            list.appendChild(listItem);
        });

        resultsContainer.appendChild(list);
    }

    function renderTimestamps(label, timestamps, videoId) {
        resultsContainer.innerHTML = `<h3>Occurrences of "${label}":</h3>`;

        timestamps.forEach((timestamp) => {
            const seconds = typeof timestamp === "string" ? parseTimestampToSeconds(timestamp) : timestamp;
            const link = document.createElement("p");
            link.textContent = `${seconds.toFixed(1)}s`;
            link.className = "timestamp-link";
            link.style.cursor = "pointer";
            link.style.textDecoration = "underline";
            link.style.color = "#007bff";
            link.onclick = () => {
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
                        args: [seconds],
                    });
                });
            };

            resultsContainer.appendChild(link);
        });

        const backBtn = document.createElement("button");
        backBtn.textContent = "Back to TOC";
        backBtn.onclick = () => renderTOC(cachedTOC, videoId);
        backBtn.style.marginTop = "10px";
        backBtn.style.cursor = "pointer";
        resultsContainer.appendChild(backBtn);
    }
});

function extractVideoId(url) {
    const match = url.match(/[?&]v=([^&]+)/);
    return match ? match[1] : null;
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
