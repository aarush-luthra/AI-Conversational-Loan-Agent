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

        // User bubble
        const userBubble = createBubble("user");
        userBubble.textContent = message;

        input.value = "";

        // Bot bubble
        const botBubble = createBubble("bot");

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
        let agentLabelAdded = false;

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

                        // 🔥 UNWRAP DOUBLE-ENCODED JSON
                        if (typeof inner === "string") {
                            inner = JSON.parse(inner);
                        }

                        const chunk = inner.chunk;

                        if (chunk?.agent && !agentLabelAdded) {
                            const label = document.createElement("div");
                            label.className = "agent-label";
                            label.textContent =
                                chunk.agent === "SalesAgent"
                                    ? "Sales Agent"
                                    : chunk.agent === "KYCAgent"
                                        ? "KYC Agent"
                                        : chunk.agent === "UnderwritingAgent"
                                            ? "Credit Analyst"
                                            : chunk.agent;

                            botBubble.appendChild(label);
                            agentLabelAdded = true;
                        }

                        if (chunk?.text) {
                            botBubble.appendChild(
                                document.createTextNode(chunk.text)
                            );
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
