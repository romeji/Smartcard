// api/auth/google.js
// Step 1: Redirect user to Google OAuth
// Vercel serverless function — no server needed

export default function handler(req, res) {
  const clientId = process.env.GOOGLE_CLIENT_ID;
  const redirectUri = process.env.VERCEL_URL
    ? `https://${process.env.VERCEL_URL}/api/auth/callback`
    : `${process.env.NEXT_PUBLIC_BASE_URL}/api/auth/callback`;

  if (!clientId) {
    return res.status(500).send("GOOGLE_CLIENT_ID manquant dans les variables d'environnement Vercel.");
  }

  const params = new URLSearchParams({
    client_id: clientId,
    redirect_uri: redirectUri,
    response_type: "code",
    scope: "openid email profile",
    access_type: "offline",
    prompt: "select_account",
    // Pass through any state (e.g. which page to return to)
    state: req.query.state || "pwa",
  });

  const googleAuthUrl = `https://accounts.google.com/o/oauth2/v2/auth?${params}`;
  res.redirect(302, googleAuthUrl);
}
