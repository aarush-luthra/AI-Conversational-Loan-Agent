const API_URL = "http://127.0.0.1:5000/chat";
let attachedFile = null;

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        attachedFile = file;
        const input = document.getElementById("user-input");
        input.value = `📎 ${file.name} attached`;
        input.placeholder = "Add a message or press send to upload...";
        
        // Change attach button color to indicate file is attached
        const attachBtn = document.getElementById("attach-btn");
        attachBtn.style.backgroundColor = "#10b981";
    }
}

async function sendMessage(event) {
    if (event) event.preventDefault();
    
    const input = document.getElementById("user-input");
    const msg = input.value.trim();
    
    // Allow sending if there's a message OR a file attached
    if (!msg && !attachedFile) return;

    // Display user message
    const displayMsg = attachedFile ? `${msg}\n📎 Uploaded: ${attachedFile.name}` : msg;
    addMessage(displayMsg, "user");
    input.value = "";
    input.placeholder = "Ask about loans or upload payslip...";

    // Add loading bubble
    const loadingId = "loading-" + Date.now();
    addMessage("", "bot temporary", loadingId);

    try {
        console.log("🚀 Starting request...", { hasFile: !!attachedFile, msg });
        let res;
        
        if (attachedFile) {
            // Send as multipart/form-data
            const formData = new FormData();
            formData.append("message", msg || "I'm uploading my payslip for salary verification");
            formData.append("session_id", "demo_user");
            formData.append("file", attachedFile);
            
            console.log("📤 Sending file upload...");
            res = await fetch(API_URL, {
                method: "POST",
                body: formData
            });
            
            console.log("📥 Response status:", res.status, res.statusText);
            
            // Reset file attachment
            attachedFile = null;
            document.getElementById("file-input").value = "";
            document.getElementById("attach-btn").style.backgroundColor = "";
        } else {
            // Send as JSON
            console.log("📤 Sending text message...");
            res = await fetch(API_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: msg, session_id: "demo_user" })
            });
            console.log("📥 Response status:", res.status, res.statusText);
        }

        if (!res.ok) {
            throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }

        const data = await res.json();
        console.log("✅ Received response data:", data);

        // Remove loading bubble
        const loadingBubble = document.getElementById(loadingId);
        if (loadingBubble) {
            console.log("🗑️ Removing loading bubble");
            loadingBubble.remove();
        }

        // Handle Object vs String
        let responseText = data.response;
        if (typeof responseText === 'object') {
            console.log("⚠️ Response is object, stringifying");
            responseText = JSON.stringify(responseText);
        }

        console.log("📝 About to display:", responseText.substring(0, 100));
        addMessage(responseText, "bot");
        console.log("✅ Message displayed successfully");

    } catch (e) {
        console.error("❌ ERROR in sendMessage:", e);
        console.error("❌ Error stack:", e.stack);
        document.getElementById(loadingId)?.remove();
        addMessage("Error: " + e.message, "bot error");
    }
}

function addMessage(text, type, id = null) {
    const box = document.getElementById("chat-box");
    const div = document.createElement("div");

    console.log("🔵 addMessage called:", { text: text?.substring(0, 50), type, hasBox: !!box });

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
            try {
                // 1. Parse Markdown to HTML
                let htmlContent = typeof marked !== 'undefined' && marked.parse 
                    ? marked.parse(text) 
                    : text.replace(/\n/g, '<br>');

                // 2. Custom cleanup: Make raw links clickable
                const linkRegex = /(?<!href=")(https?:\/\/[^\s<]+)/g;
                const linkReplacement = `<a href="$1" target="_blank" class="download-link">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                    Open Document
                </a>`;
                htmlContent = htmlContent.replace(linkRegex, linkReplacement);

                div.innerHTML = htmlContent;
                console.log("✅ Bot message HTML set");
            } catch (e) {
                console.error("❌ Error parsing markdown:", e);
                div.innerText = text;
            }
        } else {
            // User messages are just plain text
            div.innerText = text;
        }
    }

    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
    console.log("✅ Message appended to DOM");
}

function handleEnter(e) { 
    if (e.key === "Enter") {
        e.preventDefault();
        sendMessage();
    }
}