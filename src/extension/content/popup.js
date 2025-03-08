document.addEventListener("DOMContentLoaded", () => {
    const loginButton = document.getElementById("googleLoginBtn");
    const statusMessage = document.getElementById("statusMessage");
  
    // Check if the user is already logged in
    chrome.storage.local.get(["accessToken"], (result) => {
      if (result.accessToken) {
        // User already has an access token
        loginButton.textContent = "Already Logged In";
        loginButton.disabled = true;
        statusMessage.textContent = "You are already authenticated.";
      } else {
        // User is not logged in; set up login flow
        loginButton.addEventListener("click", () => {
          // Send a message to background.js to start the login flow
          chrome.runtime.sendMessage({ action: "login" }, (response) => {
            if (response && response.status === "error") {
              statusMessage.textContent = "Login failed: " + response.message;
            } else {
              statusMessage.textContent = "Login flow started. Please complete in the browser window.";
            }
          });
        });
      }
    });
  });
  