console.log("Vidify content script loaded!");

// Track if we've injected our script
let scriptInjected = false;

// Function to inject a simple script to directly control YouTube player
function injectDirectController() {
  if (scriptInjected) return;
  
  const script = document.createElement('script');
  script.textContent = `
    // Create a global function that can be called from the extension
    window.jumpToTime = function(seconds) {
      try {
        console.log("Attempting to jump to " + seconds + " seconds");
        
        // Get the YouTube player
        const player = document.querySelector('#movie_player');
        if (player && typeof player.seekTo === 'function') {
          // Use YouTube's native seekTo method
          player.seekTo(seconds, true);
          
          // Make sure video is playing
          if (typeof player.playVideo === 'function') {
            player.playVideo();
          }
          
          // Show visual feedback
          const notification = document.createElement('div');
          notification.textContent = 'Jumped to ' + seconds + ' seconds';
          notification.style.position = 'fixed';
          notification.style.bottom = '70px';
          notification.style.left = '50%';
          notification.style.transform = 'translateX(-50%)';
          notification.style.backgroundColor = 'rgba(0, 123, 255, 0.9)';
          notification.style.color = 'white';
          notification.style.padding = '10px 20px';
          notification.style.borderRadius = '5px';
          notification.style.zIndex = '9999';
          notification.style.fontWeight = 'bold';
          
          document.body.appendChild(notification);
          
          // Remove notification after 2 seconds
          setTimeout(() => {
            if (notification.parentNode) {
              notification.parentNode.removeChild(notification);
            }
          }, 2000);
          
          return true;
        } else {
          // Fallback to video element
          const video = document.querySelector('video');
          if (video) {
            video.currentTime = seconds;
            if (video.paused) video.play();
            return true;
          }
        }
        
        return false;
      } catch (e) {
        console.error("Error jumping to time:", e);
        return false;
      }
    };
    
    console.log("YouTube controller injected");
  `;
  
  document.head.appendChild(script);
  scriptInjected = true;
  console.log("Direct YouTube controller injected");
}

// Inject controller soon after page loads
setTimeout(injectDirectController, 1500);

// Listen for messages from the extension popup or background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log("Content script received message:", request);
  
  if (request.action === "seekToTimestamp") {
    // Make sure our controller is injected
    if (!scriptInjected) {
      injectDirectController();
    }
    
    // Parse the timestamp to get seconds
    let seconds = parseTimestamp(request.timestamp);
    console.log(`Seeking to ${seconds} seconds`);
    
    // Execute our injected function
    try {
      const result = window.jumpToTime(seconds);
      sendResponse({
        status: result ? "Success" : "Failed to control player",
        timestamp: seconds
      });
    } catch (error) {
      console.error("Error executing jumpToTime:", error);
      sendResponse({
        status: "Error: " + error.message,
        timestamp: seconds
      });
    }
    
    return true;
  }
  
  return false;
});

// Helper function to parse timestamps in different formats
function parseTimestamp(timestamp) {
  // Remove 's' suffix if present
  timestamp = timestamp.toString().replace(/s$/, '');
  
  // Try parsing as a simple float first
  let seconds = parseFloat(timestamp);
  if (!isNaN(seconds)) {
    return seconds;
  }
  
  // Parse timestamp in format "00:01:23.456"
  const match = timestamp.match(/^(?:(\d+):)?(\d+):(\d+)(?:\.(\d+))?$/);
  if (match) {
    const hours = match[1] ? parseInt(match[1], 10) : 0;
    const minutes = parseInt(match[2], 10);
    const seconds = parseInt(match[3], 10);
    const milliseconds = match[4] ? parseInt(match[4], 10) / Math.pow(10, match[4].length) : 0;
    
    return hours * 3600 + minutes * 60 + seconds + milliseconds;
  }
  
  // If all else fails, return 0
  console.error(`Failed to parse timestamp: ${timestamp}`);
  return 0;
}