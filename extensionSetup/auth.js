const BACKEND_URL = "http://localhost:8000";

// Called after Google OAuth succeeds — saves token from our backend
async function handleGoogleLogin() {
    return new Promise((resolve, reject) => {
        chrome.identity.getAuthToken({ interactive: true }, async (googleToken) => {
            if (chrome.runtime.lastError) {
                console.error("[AdaptiveSec] Google OAuth failed:", chrome.runtime.lastError);
                reject(chrome.runtime.lastError);
                return;
            }

            try {
                // Send Google token to our backend to get our own JWT
                const resp = await fetch(`${BACKEND_URL}/auth/google`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ token: googleToken })
                });

                const data = await resp.json();

                // Save our JWT, user_id, and display name to Chrome storage
                await chrome.storage.local.set({
                    token: data.access_token,
                    user_id: data.user_id,
                    user_name: data.name,
                    user_email: data.email
                });

                console.log("[AdaptiveSec] Logged in as:", data.name);
                resolve(data);
            } catch (err) {
                console.error("[AdaptiveSec] Backend auth failed:", err);
                reject(err);
            }
        });
    });
}

// Check if user is already logged in
async function checkAuthStatus() {
    const { token, user_id, user_name } = await chrome.storage.local.get([
        "token", "user_id", "user_name"
    ]);
    return { isLoggedIn: !!(token && user_id), token, user_id, user_name };
}

// Logout — clear all stored auth data
async function logout() {
    await chrome.storage.local.remove(["token", "user_id", "user_name", "user_email"]);
    console.log("[AdaptiveSec] Logged out");
}