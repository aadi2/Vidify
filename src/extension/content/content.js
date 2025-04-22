console.log("Vidify content script loaded!");

// Detect YouTube video
const videoElement = document.querySelector("video");
let overlayContainer = null;
let eventListeners = [];

// Create overlay for displaying search results
function initializeOverlay() {
    if (videoElement && !overlayContainer) {
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
        overlayContainer.style.maxWidth = "300px";
        overlayContainer.style.overflowY = "auto";
        document.body.appendChild(overlayContainer);
    }
}

if (videoElement) {
    initializeOverlay();
}

// Clean up function for proper resource management
function cleanup() {
    // Remove event listeners
    eventListeners.forEach(listener => {
        chrome.runtime.onMessage.removeListener(listener.callback);
    });
    eventListeners = [];
    
    // Remove DOM elements
    cleanupOverlay();
}

function cleanupOverlay() {
    if (overlayContainer && overlayContainer.parentNode) {
        overlayContainer.parentNode.removeChild(overlayContainer);
        overlayContainer = null;
    }
}

// Listen for messages from the background script
const messageListener = (request, sender, sendResponse) => {
    if (request.action === "displayResults") {
        if (!overlayContainer) {
            initializeOverlay();
        }
        displayResults(request.data);
        sendResponse({ status: "Results displayed" });
    } else if (request.action === "cleanup") {
        cleanup();
        sendResponse({ status: "Cleaned up" });
    }
};

// Store listener reference for cleanup
chrome.runtime.onMessage.addListener(messageListener);
eventListeners.push({ type: 'message', callback: messageListener });

/**
 * Display search results on the video overlay.
 * @param {Array} results - List of timestamps and objects found in the video
 */
function displayResults(results) {
    if (!overlayContainer) {
        initializeOverlay();
    }
    
    // Use DocumentFragment for better performance
    const fragment = document.createDocumentFragment();
    
    const heading = document.createElement("h3");
    heading.textContent = "Search Results:";
    fragment.appendChild(heading);

    if (!results || results.length === 0) {
        const noResults = document.createElement("p");
        noResults.textContent = "No results found.";
        fragment.appendChild(noResults);
    } else {
        results.forEach(result => {
            const item = document.createElement("p");
            item.textContent = `Object: ${result.object} at ${result.timestamp}s`;
            item.style.cursor = "pointer";
            item.style.textDecoration = "underline";
            
            // Use a closure to prevent memory leaks
            const seekHandler = () => seekToTimestamp(result.timestamp);
            item.addEventListener('click', seekHandler);
            
            fragment.appendChild(item);
        });
    }

    const closeButton = document.createElement("button");
    closeButton.textContent = "Close Results";
    closeButton.style.marginTop = "10px";
    closeButton.style.cursor = "pointer";
    
    // Use proper event listener instead of inline onclick
    const closeHandler = () => {
        while (overlayContainer.firstChild) {
            overlayContainer.removeChild(overlayContainer.firstChild);
        }
    };
    closeButton.addEventListener('click', closeHandler);
    
    fragment.appendChild(closeButton);
    
    // Clear current content and append the fragment
    while (overlayContainer.firstChild) {
        overlayContainer.removeChild(overlayContainer.firstChild);
    }
    overlayContainer.appendChild(fragment);
}

/**
 * Seek video to specified timestamp.
 * @param {string} timestamp - Time in seconds
 */
function seekToTimestamp(timestamp) {
    if (videoElement) {
        videoElement.currentTime = parseFloat(timestamp);
        videoElement.play();
    }
}

// Handle page unload by cleaning up resources
window.addEventListener('unload', cleanup);

// Add cleanup for when page changes without full navigation (SPA behavior)
const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
        if (mutation.type === 'childList' && mutation.removedNodes.length > 0) {
            for (const node of mutation.removedNodes) {
                if (node.contains && node.contains(videoElement)) {
                    cleanup();
                    break;
                }
            }
        }
    }
});

// Start observing
observer.observe(document.body, { childList: true, subtree: true });