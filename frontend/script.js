const API_URL = "http://127.0.0.1:5000/chat";


async function sendMessage() {
    const input = document.getElementById("user-input");
    const msg = input.value.trim();
    if (!msg) return;

    addMessage(msg, "user");
    input.value = "";

    // Add loading bubble
    const loadingId = "loading-" + Date.now();
    addMessage("", "bot temporary", loadingId);

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
        addMessage("Error connecting to server. Please try again.", "bot error");
    }
}

function addMessage(text, type, id = null) {
    const box = document.getElementById("chat-box");
    const div = document.createElement("div");

    // Check if it's a loading/typing bubble or a real message
    if (type.includes("temporary")) {
        div.className = `message ${type}`;
        div.id = id;
        div.innerHTML = `
            <div class="typing-dots">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
            </div>
        `;
    } else {
        div.className = `message ${type}`;
        if (id) div.id = id;

        if (type.includes("bot")) {
            // 1. Parse Markdown to HTML
            let htmlContent = marked.parse(text);

            // 2. Custom cleanup: Make raw links clickable

            const linkRegex = /(?<!href=")(https?:\/\/[^\s<]+)/g;
            const linkReplacement = `<a href="$1" target="_blank" class="download-link">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                Open Document
            </a>`;
            htmlContent = htmlContent.replace(linkRegex, linkReplacement);

            div.innerHTML = htmlContent;
        } else {
            // User messages are just plain text
            div.innerText = text;
        }
    }

    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
}

function handleEnter(e) { if (e.key === "Enter") sendMessage(); }