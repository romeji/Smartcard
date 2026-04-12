// api/auth/callback.js — Step 2: Exchange code for Firebase custom token
import { initializeApp, cert, getApps } from "firebase-admin/app";
import { getAuth } from "firebase-admin/auth";

const GOOGLE_CLIENT_ID = "126521073547-ul3fugt7usg7nudf6bgroh2p3t2ugks2.apps.googleusercontent.com";
const GOOGLE_CLIENT_SECRET = "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";
const BASE_URL = "https://smartcard-eosin.vercel.app";
const REDIRECT_URI = BASE_URL + "/api/auth/callback";

function getAdmin() {
  if (getApps().length > 0) return getApps()[0];
  return initializeApp({
    credential: cert({
      projectId: process.env.FIREBASE_PROJECT_ID,
      privateKey: process.env.FIREBASE_PRIVATE_KEY?.replace(/\\n/g, "\n"),
      clientEmail: process.env.FIREBASE_CLIENT_EMAIL,
    }),
  });
}

export default async function handler(req, res) {
  const { code, error } = req.query;

  if (error) {
    return res.redirect(302, BASE_URL + "/#auth_error=" + encodeURIComponent("Google refusé : " + error));
  }
  if (!code) {
    return res.redirect(302, BASE_URL + "/#auth_error=" + encodeURIComponent("Pas de code OAuth."));
  }

  try {
    // 1. Échanger le code contre les tokens Google
    const tokenRes = await fetch("https://oauth2.googleapis.com/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        code,
        client_id: GOOGLE_CLIENT_ID,
        client_secret: GOOGLE_CLIENT_SECRET,
        redirect_uri: REDIRECT_URI,
        grant_type: "authorization_code",
      }),
    });
    const tokenData = await tokenRes.json();

    if (tokenData.error) {
      console.error("Token error:", tokenData);
      return res.redirect(302, BASE_URL + "/#auth_error=" + encodeURIComponent("Token échoué : " + tokenData.error_description));
    }

    // 2. Récupérer le profil Google
    const userRes = await fetch("https://www.googleapis.com/oauth2/v3/userinfo", {
      headers: { Authorization: "Bearer " + tokenData.access_token },
    });
    const user = await userRes.json();

    if (!user.sub) {
      return res.redirect(302, BASE_URL + "/#auth_error=" + encodeURIComponent("Profil Google introuvable."));
    }

    // 3. Créer/récupérer l'utilisateur Firebase
    getAdmin();
    const firebaseAuth = getAuth();
    const uid = "google_" + user.sub;

    try {
      await firebaseAuth.getUser(uid);
    } catch {
      await firebaseAuth.createUser({
        uid,
        email: user.email,
        displayName: user.name || user.email,
        photoURL: user.picture || "",
        emailVerified: true,
      });
    }

    // Sync email/name if changed
    await firebaseAuth.updateUser(uid, {
      email: user.email,
      displayName: user.name || user.email,
      emailVerified: true,
    }).catch(() => {});

    // 4. Créer le custom token Firebase (valide 1h)
    const customToken = await firebaseAuth.createCustomToken(uid, {
      email: user.email,
      name: user.name || "",
    });

    // 5. Rediriger vers la PWA avec le token dans le hash
    const hashData = [
      "firebase_custom_token=" + encodeURIComponent(customToken),
      "user_email=" + encodeURIComponent(user.email || ""),
      "user_name=" + encodeURIComponent(user.name || ""),
    ].join("&");

    return res.redirect(302, BASE_URL + "/#" + hashData);

  } catch (err) {
    console.error("Callback error:", err);
    return res.redirect(302, BASE_URL + "/#auth_error=" + encodeURIComponent("Erreur serveur : " + err.message));
  }
}
