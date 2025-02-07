console.log("Vidify content script loaded!");

// Detect YouTube video
const videoElement = document.querySelector("video");
let overlayContainer;

// Create overlay for displaying search results
if (videoElement) {
    console.log("YouTube video detected.");

    // Dynamically create an overlay container
    overlayContainer = document.createElement("div");
    overlayContainer.style.position = "absolute";
    overlayContainer.style.top = "20px";
    overlayContainer.style.right = "20px";
    overlayContainer.style.zIndex = "1000";
    overlayContainer.style.backgroundColor = "rgba(0, 0, 0, 0.7)";
    overlayContainer.style.color = "#fff";
    overlayContainer.style.padding = "10px";
    overlayContainer.style.borderRadius = "5px";
    document.body.appendChild(overlayContainer);
}

// Listen for messages from the background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "displayResults") {
        displayResults(request.data);
    }
    sendResponse({ status: "Results displayed" });
});

/**
 * Display search results on the video overlay.
 * @param {Array} results - List of timestamps and objects found in the video
 */
function displayResults(results) {
    overlayContainer.innerHTML = "<h3>Search Results:</h3>";
    results.forEach(result => {
        const item = document.createElement("p");
        item.textContent = `Object: ${result.object} at ${result.timestamp}s`;
        overlayContainer.appendChild(item);
    });
}
