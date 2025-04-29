
function getCurrentYouTubeURL() {
    return window.location.href;
  }
  
  function renderTOC(data) {
    const container = document.getElementById("toc-container");
    container.innerHTML = "";
  
    if (!Object.keys(data).length) {
      container.innerHTML = "<p>No objects detected.</p>";
      return;
    }
  
    for (const [objectName, timestamps] of Object.entries(data)) {
      const section = document.createElement("div");
      section.className = "toc-object";
      section.innerHTML = `<h3>${objectName}</h3>`;
  
      const list = document.createElement("ul");
  
      timestamps.forEach(ts => {
        const li = document.createElement("li");
        li.textContent = `${ts.toFixed(2)}s`;
        li.style.cursor = "pointer";
        li.onclick = () => {
          const video = document.querySelector("video");
          if (video) video.currentTime = ts;
        };
        list.appendChild(li);
      });
  
      section.appendChild(list);
      container.appendChild(section);
    }
  }
  
  async function fetchObjectTOC() {
    const ytUrl = getCurrentYouTubeURL();
  
    try {
      const response = await fetch(`http://127.0.0.1:8001/object_search?yt_url=${encodeURIComponent(ytUrl)}`);
      const data = await response.json();
  
      if (response.ok && data.results) {
        renderTOC(data.results);
      } else {
        document.getElementById("toc-container").innerHTML = `<p>${data.message || "Error fetching TOC"}</p>`;
      }
    } catch (error) {
      document.getElementById("toc-container").innerHTML = `<p>Failed to fetch objects: ${error.message}</p>`;
    }
  }
  
  document.addEventListener("DOMContentLoaded", fetchObjectTOC);
  