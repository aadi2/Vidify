document.addEventListener("DOMContentLoaded", () => {
  const statusMessage = document.getElementById("statusMessage");

  // Check for the cached access token
  chrome.storage.local.get(["accessToken"], (result) => {
    if (result.accessToken) {
      statusMessage.textContent = "You are already authenticated.";
    } else {
      statusMessage.textContent = "Not authenticated yet. The extension will authenticate automatically on startup.";
    }
  });
});
