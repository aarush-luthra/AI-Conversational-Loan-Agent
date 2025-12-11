const API_URL = "http://localhost:5000/chat"; 

async function sendMessage() {
    const input = document.getElementById("user-input");
    const msg = input.value.trim();
    if (!msg) return;

    addMessage(msg, "user");
    input.value = "";
    
    const loadingId = "loading-" + Date.now();
    addMessage("Agents are working...", "bot temporary", loadingId);

    try {
        const res = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: msg, session_id: "multi_agent_demo" })
        });
        
        const data = await res.json();
        document.getElementById(loadingId)?.remove();
        
        let responseText = data.response;
        if (typeof responseText === 'object') {
            responseText = JSON.stringify(responseText);
        }
        addMessage(responseText, "bot");

    } catch (e) {
        document.getElementById(loadingId)?.remove();
        addMessage("⚠️ Connection Error.", "bot error");
    }
}

function addMessage(text, type, id = null) {
    const box = document.getElementById("chat-box");
    const div = document.createElement("div");
    div.className = `message ${type}`;
    if (id) div.id = id;

    if (type.includes("bot") && !type.includes("temporary")) {
        // Parse Markdown
        let htmlContent = marked.parse(text);
        // Make links clickable buttons
        htmlContent = htmlContent.replace(/(?<!href=")(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" class="download-link">📄 Open Document</a>');
        div.innerHTML = htmlContent;
    } else {
        div.innerText = text;
    }
    
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
}

function handleEnter(e) { if (e.key === "Enter") sendMessage(); }