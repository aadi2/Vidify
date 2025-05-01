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
        resultsContainer.innerHTML = `<h3 style='font-size: 1.3em; margin-bottom: 12px;'>Results:</h3>`;

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

                    const card = document.createElement("div");
                    card.innerHTML = `<strong>${label}</strong> at ${seconds.toFixed(1)}s`;
                    card.className = "timestamp-link";
                    card.style.cursor = "pointer";
                    card.style.borderRadius = "6px";
                    card.style.padding = "10px";
                    card.style.textAlign = "center";
                    card.style.marginBottom = "4px";
                    card.style.fontSize = "1.2em";
                    card.style.backgroundColor = "#ffde79";
                    card.style.transition = "transform 0.15s ease, background-color 0.2s ease";

                    card.onmouseover = () => {
                        card.style.transform = "scale(1.03)";
                        card.style.backgroundColor = "#f0f0f0";
                    };
                    card.onmouseout = () => {
                        card.style.transform = "scale(1)";
                        card.style.backgroundColor = "#ffde79";
                    };
                    card.onclick = () => {
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
                    resultsContainer.appendChild(card);
                });
            } else if (result.timestamp !== undefined) {
                const seconds = typeof result.timestamp === "string" ? parseTimestampToSeconds(result.timestamp) : result.timestamp;

                const card = document.createElement("div");
                card.innerHTML = `<strong>${label}</strong> at ${seconds.toFixed(1)}s`;
                card.className = "timestamp-link";
                card.style.cursor = "pointer";
                card.style.borderRadius = "6px";
                card.style.padding = "10px";
                card.style.textAlign = "center";
                card.style.marginBottom = "4px";
                card.style.fontSize = "1.2em";
                card.style.backgroundColor = "#ffde79";
                card.style.transition = "transform 0.15s ease, background-color 0.2s ease";

                card.onmouseover = () => {
                    card.style.transform = "scale(1.03)";
                    card.style.backgroundColor = "#f0f0f0";
                };
                card.onmouseout = () => {
                    card.style.transform = "scale(1)";
                    card.style.backgroundColor = "#ffde79";
                };
                card.onclick = () => {
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
                resultsContainer.appendChild(card);
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
        resultsContainer.innerHTML = "<h3 style='font-size: 1.3em; margin-bottom: 12px;'>Detected Objects:</h3>";

        const list = document.createElement("div");
        tocData.results.forEach((obj) => {
            const listItem = document.createElement("div");
            listItem.textContent = obj.object;
            listItem.style.cursor = "pointer";
            listItem.style.padding = "8px 12px";
            listItem.style.marginBottom = "4px";
            listItem.style.fontSize = "1.2em";
            listItem.style.borderRadius = "6px";
            listItem.style.backgroundColor = "#ffde79";
            listItem.style.transition = "transform 0.15s ease, background-color 0.2s ease";

            // Optional hover effect
            listItem.onmouseover = () => {
                listItem.style.transform = "scale(1.03)";
                listItem.style.backgroundColor = "#f0f0f0";
            };
            listItem.onmouseout = () => {
                listItem.style.transform = "scale(1)";
                listItem.style.backgroundColor = "#ffde79";
            };

            listItem.onclick = () => {
                renderTimestamps(obj.object, obj.timestamps, videoId);
            };

            list.appendChild(listItem);
        });

        resultsContainer.appendChild(list);

        statusMessage.textContent = "";
    }

    function renderTimestamps(label, timestamps, videoId) {
        resultsContainer.innerHTML = `<h3 style="font-size: 1.3em; margin-bottom: 12px;">Occurrences of "${label}":</h3>`;

        timestamps.forEach((timestamp) => {
            const seconds = typeof timestamp === "string" ? parseTimestampToSeconds(timestamp) : timestamp;
            const card = document.createElement("div");
            card.textContent = `${seconds.toFixed(1)}s`;
            card.className = "timestamp-link";
            card.style.cursor = "pointer";
            card.style.borderRadius = "6px";
            card.style.padding = "10px";
            card.style.textAlign = "center";
            card.style.marginBottom = "4px"
            card.style.fontSize = "1.2em";
            card.style.backgroundColor = "#ffde79";
            card.style.transition = "transform 0.15s ease, background-color 0.2s ease";

            card.onmouseover = () => {
                card.style.transform = "scale(1.03)";
                card.style.backgroundColor = "#f0f0f0";
            };
            card.onmouseout = () => {
                card.style.transform = "scale(1)";
                card.style.backgroundColor = "#ffde79";
            };
            card.onclick = () => {
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

            resultsContainer.appendChild(card);
        });

        const backBtn = document.createElement("button");
        backBtn.textContent = "Back to TOC";
        backBtn.onclick = () => renderTOC(cachedTOC, videoId);

        backBtn.style.display = "block";
        backBtn.style.width = "100%";
        backBtn.style.boxSizing = "border-box";
        backBtn.style.marginTop = "16px";
        backBtn.style.padding = "10px";
        backBtn.style.border = "none";
        backBtn.style.borderRadius = "6px";
        backBtn.style.color = "#fff";
        backBtn.style.fontSize = "1.1em";
        backBtn.style.cursor = "pointer";
        backBtn.style.backgroundColor = "transparent"
        backBtn.style.transition = "transform 0.15s ease, background-color 0.2s ease";

        backBtn.onmouseover = () => {
            backBtn.style.transform = "scale(1.03)";
            backBtn.style.backgroundColor = "#0066ff";
        };
        backBtn.onmouseout = () => {
            backBtn.style.transform = "scale(1.03)";
            backBtn.style.backgroundColor = "transparent";
        };
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
