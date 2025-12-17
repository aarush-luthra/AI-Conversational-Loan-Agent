document.addEventListener("DOMContentLoaded", () => {
    const chat = document.getElementById("chat");
    const input = document.getElementById("messageInput");
    const sendBtn = document.getElementById("send-btn");

    if (!chat || !input || !sendBtn) {
        console.error("❌ Chat UI elements missing");
        return;
    }

    function createBubble(sender) {
        const bubble = document.createElement("div");
        bubble.className = `message ${sender}`;
        chat.appendChild(bubble);
        chat.scrollTop = chat.scrollHeight;
        return bubble;
    }

    async function sendMessage() {
        const message = input.value.trim();
        if (!message) return;

        /* ---------- User Bubble ---------- */
        const userBubble = createBubble("user");
        userBubble.textContent = message;
        input.value = "";

        /* ---------- Bot Bubble ---------- */
        const botBubble = createBubble("bot");

        let fullText = "";
        let agentName = null;
        let agentDetected = false;

        const response = await fetch("http://127.0.0.1:5000/chat/stream", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message,
                session_id: "web"
            })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop();

            for (const line of lines) {
                if (!line.startsWith("data:")) continue;

                const payload = line.replace("data:", "").trim();
                if (!payload) continue;

                try {
                    const outer = JSON.parse(payload);

                    if (outer.chunk) {
                        let inner = outer.chunk;

                        // Handle double-encoded JSON
                        if (typeof inner === "string") {
                            inner = JSON.parse(inner);
                        }

                        const chunk = inner.chunk;

                        /* ---------- Agent Detection ---------- */
                        if (chunk?.agent && !agentDetected) {
                            agentName =
                                chunk.agent === "SalesAgent"
                                    ? "Sales Agent"
                                    : chunk.agent === "KYCAgent"
                                        ? "KYC Agent"
                                        : chunk.agent === "UnderwritingAgent"
                                            ? "Credit Analyst"
                                            : chunk.agent;

                            agentDetected = true;
                        }

                        /* ---------- Streaming Markdown ---------- */
                        if (chunk?.text) {
                            fullText += chunk.text;

                            // Clear and re-render (stream-safe)
                            botBubble.innerHTML = "";

                            // Agent label (small + colored)
                            if (agentName) {
                                const label = document.createElement("div");
                                label.className = "agent-label";
                                label.textContent = agentName;
                                botBubble.appendChild(label);
                            }

                            // Markdown-rendered content
                            const content = document.createElement("div");
                            content.innerHTML = marked.parse(fullText);
                            botBubble.appendChild(content);

                            chat.scrollTop = chat.scrollHeight;
                        }
                    }

                    if (outer.done) return;
                } catch (err) {
                    console.error("❌ Stream parse error:", err, payload);
                }
            }
        }
    }

    sendBtn.addEventListener("click", sendMessage);
    input.addEventListener("keydown", e => {
        if (e.key === "Enter") sendMessage();
    });
});
