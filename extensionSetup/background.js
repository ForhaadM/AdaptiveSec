const BACKEND_URL = "http://localhost:8000";
const SIM_URL_PATTERN = "adaptive-sec-sim";

chrome.runtime.onInstalled.addListener(() => {
    console.log("AdaptiveSec extension installed");
    initWebSocket();
});


chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "SIMULATION_CLICK") {
        handleSimulationClick(message.data);
    }
});


async function handleSimulationClick({ url, pageContext, timestamp }) {
    // AC5: only fire for AdaptiveSec simulation URLs
    if (!url.includes(SIM_URL_PATTERN)) {
        console.log("[AdaptiveSec] Not a simulation URL, ignoring:", url);
        return;
    }

    try {

        const { token, user_id } = await chrome.storage.local.get(["token", "user_id"]);

        if (!token || !user_id) {
            console.error("[AdaptiveSec] No token found — user not authenticated");
            return;
        }


        const payload = {
            user_id: user_id,
            url: url,
            page_context: pageContext || "",
            timestamp: timestamp || new Date().toISOString(),
        };


        fetch(`${BACKEND_URL}/api/v1/telemetry/click`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        })
            .then(resp => {
                console.log("[AdaptiveSec] Telemetry fired →", resp.status);
            })
            .catch(err => {

                console.error("[AdaptiveSec] Backend unreachable:", err.message);
            });

    } catch (err) {

        console.error("[AdaptiveSec] handleSimulationClick error:", err.message);
    }
}


function initWebSocket() {
    chrome.storage.local.get(["token", "user_id"], ({ token, user_id }) => {
        if (!token || !user_id) {
            console.log("[AdaptiveSec] No token yet, skipping WebSocket init");
            return;
        }
        const ws = new WebSocket(
            `ws://localhost:8000/ws/v1/alerts/${user_id}?token=${token}`
        );
        ws.onopen = () => console.log("[AdaptiveSec] WebSocket connected");
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log("[AdaptiveSec] Score update received:", data);

            chrome.storage.local.set({ latest_alert: data });
        };
        ws.onclose = () => {
            console.log("[AdaptiveSec] WebSocket closed, reconnecting in 5s...");
            setTimeout(initWebSocket, 5000);
        };
        ws.onerror = (err) => {
            console.error("[AdaptiveSec] WebSocket error:", err);
        };
    });
}

async function createOffscreenDocument() {
    await chrome.offscreen.createDocument({
        url: "offscreen.html",
        reasons: ["DOM_SCRAPING"],
        justification: "Process page content for phishing detection"
    });
}