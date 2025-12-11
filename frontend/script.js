const API_URL = "http://localhost:5000/chat"; 

async function sendMessage() {
    const input = document.getElementById("user-input");
    const msg = input.value.trim();
    if (!msg) return;

    addMessage(msg, "user");
    input.value = "";
    
    // Add loading bubble
    const loadingId = "loading-" + Date.now();
    addMessage("Typing...", "bot temporary", loadingId);

    try {
        const res = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: msg, session_id: "demo_user" })
        });
        
        const data = await res.json();
        
        // Remove loading bubble
        const loadingBubble = document.getElementById(loadingId);
        if (loadingBubble) loadingBubble.remove();

        // Handle Object vs String
        let responseText = data.response;
        if (typeof responseText === 'object') {
            responseText = JSON.stringify(responseText);
        }
        
        addMessage(responseText, "bot");

    } catch (e) {
        document.getElementById(loadingId)?.remove();
        console.error(e);
        addMessage("⚠️ Error connecting to server.", "bot error");
    }
}

function addMessage(text, type, id = null) {
    const box = document.getElementById("chat-box");
    const div = document.createElement("div");
    div.className = `message ${type}`;
    if (id) div.id = id;

    if (type.includes("bot") && !type.includes("temporary")) {
        // --- THE MAGIC PART ---
        // 1. Parse Markdown to HTML (Handling Bold, Lists, etc.)
        let htmlContent = marked.parse(text);
        
        // 2. Custom cleanup: Make raw links clickable if the AI didn't format them
        // (This regex finds http links that aren't already inside an <a> tag)
        const linkRegex = /(?<!href=")(https?:\/\/[^\s<]+)/g;
        htmlContent = htmlContent.replace(linkRegex, '<a href="$1" target="_blank" class="download-link">📄 Open Document</a>');

        div.innerHTML = htmlContent;
    } else {
        // User messages are just plain text
        div.innerText = text;
    }
    
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
}

function handleEnter(e) { if (e.key === "Enter") sendMessage(); }