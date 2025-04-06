/**
 * YouTube Navigator - Direct interaction with YouTube's player API
 * This script is injected into the YouTube page context to enable
 * timestamp navigation without causing page refreshes.
 */

// Store reference to the player
let youtubePlayer = null;

// Function to find YouTube's player and cache it
function findYouTubePlayer() {
  youtubePlayer = document.querySelector('#movie_player');
  return youtubePlayer;
}

// Create global seek function that the content script can call
window.vidifySeekTo = function(seconds) {
  try {
    // Find the player if we don't have it yet
    if (!youtubePlayer) {
      findYouTubePlayer();
    }
    
    if (youtubePlayer && typeof youtubePlayer.seekTo === 'function') {
      // YouTube's native seekTo method
      console.log("Seeking to " + seconds + " seconds using YouTube player API");
      
      // The second parameter (true) means seek and play
      youtubePlayer.seekTo(seconds, true);
      
      // Force player to play if it's paused
      if (typeof youtubePlayer.playVideo === 'function' && 
          youtubePlayer.getPlayerState() !== 1) { // 1 = playing
        youtubePlayer.playVideo();
      }
      
      return true;
    } else {
      // Fallback: try to get video element directly
      const video = document.querySelector('video');
      if (video) {
        console.log("YouTube player API not found, using video element");
        video.currentTime = seconds;
        if (video.paused) {
          video.play();
        }
        return true;
      }
      
      console.error("YouTube player not found");
      return false;
    }
  } catch (e) {
    console.error("Error in vidifySeekTo:", e);
    return false;
  }
};

// Create a promise-based version for async usage
window.vidifySeekToTime = function(seconds) {
  return new Promise((resolve) => {
    const result = window.vidifySeekTo(seconds);
    resolve(result);
  });
};

// Listen for YouTube navigation events to refresh player reference
if (typeof yt !== 'undefined' && yt.events) {
  yt.events.subscribe('navigate', function() {
    console.log("YouTube navigation detected, refreshing player reference");
    // Clear reference so it gets re-acquired
    youtubePlayer = null;
    // Wait a bit for the new page to load
    setTimeout(findYouTubePlayer, 1000);
  });
}

// Try to find the player immediately
findYouTubePlayer();

// Notify that our navigator is ready
document.dispatchEvent(new CustomEvent('vidifyNavigatorReady'));
console.log("YouTube Navigator injected and ready");