// schemaValidator.js - Validates responses from Vidify backend
// This file ensures data coming from the backend adheres to expected formats.
// Useful for catching changes in the backend API or malformed data.

// Example valid object search response:
// {
//   "results": [
//     { "object": "car", "timestamp": "35.2" },
//     { "object": "car", "timestamp": "120.5" }
//   ]
// }

/**
 * Validates the response schema for object search results.
 * Each result must contain:
 * - object (string)
 * - timestamp (string, representing seconds or time code)
 * 
 * @param {Object} data - API response data.
 * @returns {boolean} True if the response matches the expected schema, false otherwise.
 */
export function validateObjectSearchResponse(data) {
    if (!data || !Array.isArray(data.results)) {
        console.warn("Invalid object search response: results missing or not an array", data);
        return false;
    }

    return data.results.every(result => (
        isNonEmptyString(result.object) &&
        isValidTimestamp(result.timestamp)
    ));
}

/**
 * Validates the response schema for transcript search results.
 * Each result must contain:
 * - text (string, transcript snippet)
 * - timestamp (string, representing seconds or time code)
 * 
 * @param {Object} data - API response data.
 * @returns {boolean} True if the response matches the expected schema, false otherwise.
 */
export function validateTranscriptSearchResponse(data) {
    if (!data || !Array.isArray(data.results)) {
        console.warn("Invalid transcript search response: results missing or not an array", data);
        return false;
    }

    return data.results.every(result => (
        isNonEmptyString(result.text) &&
        isValidTimestamp(result.timestamp)
    ));
}

/**
 * Helper to check if a value is a non-empty string.
 * 
 * @param {*} value - Value to check.
 * @returns {boolean} True if value is a non-empty string.
 */
function isNonEmptyString(value) {
    return typeof value === "string" && value.trim().length > 0;
}

/**
 * Validates timestamp.
 * Timestamps can be either a number in string form (e.g., "35.2")
 * or a time format like "00:01:15".
 * 
 * @param {string} timestamp - Timestamp to validate.
 * @returns {boolean} True if valid.
 */
function isValidTimestamp(timestamp) {
    if (!isNonEmptyString(timestamp)) {
        return false;
    }

    // Check numeric format (seconds)
    if (/^\d+(\.\d+)?$/.test(timestamp)) {
        return true;
    }

    // Check timecode format (HH:MM:SS or MM:SS)
    const timecodeRegex = /^(\d{1,2}:)?\d{1,2}:\d{2}$/;
    return timecodeRegex.test(timestamp);
}
