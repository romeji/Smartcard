// api/auth/callback.js
// Step 2: Google redirects here after login
// Exchange code → Google tokens → Firebase custom token → redirect to PWA

import { initializeApp, cert, getApps } from "firebase-admin/app";
import { getAuth } from "firebase-admin/auth";

// Initialize Firebase Admin (once)
function getFirebaseAdmin() {
  if (getApps().length > 0) return getApps()[0];

  const serviceAccount = {
    type: "service_account",
    project_id: process.env.FIREBASE_PROJECT_ID,
    private_key_id: process.env.FIREBASE_PRIVATE_KEY_ID,
    private_key: process.env.FIREBASE_PRIVATE_KEY?.replace(/\\n/g, "\n"),
    client_email: process.env.FIREBASE_CLIENT_EMAIL,
    client_id: process.env.FIREBASE_CLIENT_ID,
    auth_uri: "https://accounts.google.com/o/oauth2/auth",
    token_uri: "https://oauth2.googleapis.com/token",
  };

  return initializeApp({ credential: cert(serviceAccount) });
}

export default async function handler(req, res) {
  const { code, error, state } = req.query;

  // Handle OAuth errors
  if (error) {
    return redirectWithError(res, "Google OAuth refusé : " + error);
  }

  if (!code) {
    return redirectWithError(res, "Pas de code OAuth reçu.");
  }

  const clientId = process.env.GOOGLE_CLIENT_ID;
  const clientSecret = process.env.GOOGLE_CLIENT_SECRET;
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || `https://${req.headers.host}`;
  const redirectUri = `${baseUrl}/api/auth/callback`;

  try {
    // Step 1: Exchange code for Google tokens
    const tokenRes = await fetch("https://oauth2.googleapis.com/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        code,
        client_id: clientId,
        client_secret: clientSecret,
        redirect_uri: redirectUri,
        grant_type: "authorization_code",
      }),
    });

    const tokenData = await tokenRes.json();

    if (tokenData.error) {
      console.error("Token exchange error:", tokenData);
      return redirectWithError(res, "Échange de token échoué : " + tokenData.error_description);
    }

    const { id_token, access_token } = tokenData;

    if (!id_token) {
      return redirectWithError(res, "Pas d'id_token reçu de Google.");
    }

    // Step 2: Get user info from Google
    const userInfoRes = await fetch("https://www.googleapis.com/oauth2/v3/userinfo", {
      headers: { Authorization: `Bearer ${access_token}` },
    });
    const userInfo = await userInfoRes.json();

    if (!userInfo.sub) {
      return redirectWithError(res, "Impossible de récupérer le profil Google.");
    }

    // Step 3: Create Firebase custom token
    getFirebaseAdmin();
    const firebaseAuth = getAuth();

    // Create or update user in Firebase
    let firebaseUser;
    try {
      firebaseUser = await firebaseAuth.getUserByEmail(userInfo.email);
    } catch {
      // User doesn't exist yet — create them
      firebaseUser = await firebaseAuth.createUser({
        uid: `google_${userInfo.sub}`,
        email: userInfo.email,
        displayName: userInfo.name,
        photoURL: userInfo.picture,
        emailVerified: true,
      });
    }

    // Create custom token (valid 1 hour)
    const customToken = await firebaseAuth.createCustomToken(firebaseUser.uid, {
      email: userInfo.email,
      name: userInfo.name,
    });

    // Step 4: Redirect back to PWA with custom token in URL hash
    // The PWA reads this hash and calls signInWithCustomToken()
    const pwaUrl = `${baseUrl}/#firebase_custom_token=${encodeURIComponent(customToken)}&user_email=${encodeURIComponent(userInfo.email)}&user_name=${encodeURIComponent(userInfo.name || "")}`;

    return res.redirect(302, pwaUrl);

  } catch (err) {
    console.error("OAuth callback error:", err);
    return redirectWithError(res, "Erreur serveur : " + err.message);
  }
}

function redirectWithError(res, msg) {
  const baseUrl = `https://${res.req?.headers?.host || "smartcard-eosin.vercel.app"}`;
  return res.redirect(302, `${baseUrl}/#auth_error=${encodeURIComponent(msg)}`);
}
