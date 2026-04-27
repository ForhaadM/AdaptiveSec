document.addEventListener("click", (event) => {
    const target = event.target.closest("a");
    if (!target) return;

    const url = target.href || "";


    if (!url.includes("adaptive-sec-sim")) return;

    console.log("[AdaptiveSec] Simulation link clicked:", url);


    chrome.runtime.sendMessage({
        type: "SIMULATION_CLICK",
        data: {
            url: url,
            pageContext: document.title + " " + document.body.innerText.slice(0, 500),
            timestamp: new Date().toISOString()
        }
    });
});