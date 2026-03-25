
chrome.runtime.onInstalled.addListener(() => {
    console.log("AdaptiveSec extension installed");
});

async function createOffscreenDocument() {
    await chrome.offscreen.createDocument({
        url: "offscreen.html",
        reasons: ["DOM_SCRAPING"],
        justification: "Process page content for phishing detection"
    });
}