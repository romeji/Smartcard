// api/auth/google.js — Step 1: Redirect to Google OAuth
export default function handler(req, res) {
  const clientId = "126521073547-ul3fugt7usg7nudf6bgroh2p3t2ugks2.apps.googleusercontent.com";
  const baseUrl = "https://smartcard-eosin.vercel.app";
  const redirectUri = baseUrl + "/api/auth/callback";

  const params = new URLSearchParams({
    client_id: clientId,
    redirect_uri: redirectUri,
    response_type: "code",
    scope: "openid email profile",
    access_type: "offline",
    prompt: "select_account",
    state: req.query.state || "pwa",
  });

  res.redirect(302, "https://accounts.google.com/o/oauth2/v2/auth?" + params);
}
