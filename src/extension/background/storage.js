// storage.js - Handles all Chrome Storage interactions for Vidify
// This centralizes all data persistence, making it easy to update and manage
// search history or other user data.

const SEARCH_HISTORY_KEY = "searchHistory";

/**
 * Adds a search result to Chrome storage under "searchHistory".
 * Ensures history does not exceed a max limit (e.g., 50 entries) to prevent unbounded growth.
 * 
 * @param {Object} searchResult - The search result object to store.
 *        Example: { videoId: 'abc123', objectName: 'car', timestamp: '00:35' }
 * @param {number} [maxHistory=50] - Maximum number of history entries to retain.
 */
export function storeSearchResult(searchResult, maxHistory = 50) {
    if (!isValidSearchResult(searchResult)) {
        console.error("Invalid search result format", searchResult);
        return;
    }

    chrome.storage.local.get([SEARCH_HISTORY_KEY], (result) => {
        let history = result[SEARCH_HISTORY_KEY] || [];

        history.push(searchResult);

        // Trim history to max entries
        if (history.length > maxHistory) {
            history = history.slice(-maxHistory);
        }

        chrome.storage.local.set({ [SEARCH_HISTORY_KEY]: history }, () => {
            console.log("Search result stored in history:", searchResult);
        });
    });
}

/**
 * Retrieves search history from Chrome storage.
 * 
 * @param {function(Array<Object>):void} callback - Called with array of search history objects.
 */
export function getSearchHistory(callback) {
    chrome.storage.local.get([SEARCH_HISTORY_KEY], (result) => {
        callback(result[SEARCH_HISTORY_KEY] || []);
    });
}

/**
 * Clears all search history from Chrome storage.
 * 
 * @param {function():void} [callback] - Optional callback to be invoked after clearing.
 */
export function clearSearchHistory(callback) {
    chrome.storage.local.remove([SEARCH_HISTORY_KEY], () => {
        console.log("Search history cleared.");
        if (callback) callback();
    });
}

/**
 * Validates the format of a search result before saving.
 * 
 * @param {Object} result - The search result to validate.
 * @returns {boolean} True if valid, false otherwise.
 */
function isValidSearchResult(result) {
    return (
        result &&
        typeof result.videoId === 'string' &&
        typeof result.objectName === 'string' &&
        typeof result.timestamp === 'string'
    );
}
