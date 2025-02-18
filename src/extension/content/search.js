document.addEventListener("DOMContentLoaded", function() {
    const searchButton = document.getElementById("search-button");
    const searchInput = document.getElementById("search-input");
    const resultsContainer = document.getElementById("results-container");

    searchButton.addEventListener("click", function() {
        const query = searchInput.value.trim();
        
        if (query === "") {
            alert("Please enter a search term.");
            return;
        }

        // Placeholder for search logic
        resultsContainer.innerHTML = `<p>Searching for "${query}" in the video...</p>`;

        // Simulating API response (Replace this with actual API calls)
        setTimeout(() => {
            resultsContainer.innerHTML = `<p>Found object "${query}" at timestamps: 00:35, 02:15, 04:50</p>`;
        }, 2000);
    });
});
