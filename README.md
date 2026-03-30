# SmartCart 🛒

Application de courses intelligente avec IA, synchronisation Firestore en temps réel, partage de logement et analyse de photos.

## 🚀 Déploiement GitHub Pages

Ce repo est configuré pour se déployer automatiquement sur GitHub Pages à chaque push.

**Activer GitHub Pages :**
1. Settings → Pages → Source → "GitHub Actions"
2. Pusher le code → l'app est disponible sur `https://romeji.github.io/Smartcard`

## 🔧 Configuration

### Firebase (déjà intégré)
La configuration Firebase est directement dans `smartcart.html`.

**⚠️ Obligatoire — Règles Firestore :**
```
rules_version = '2';
service cloud.firestore {
  match /databases/{db}/documents {
    match /users/{uid} {
      allow read, write: if request.auth.uid == uid;
    }
    match /households/{code} {
      allow read, write: if request.auth != null;
    }
  }
}
```

**⚠️ Obligatoire — Domaines autorisés Firebase Auth :**
Ajoutez `romeji.github.io` dans Firebase Console → Authentication → Settings → Authorized domains.

### Anthropic API (pour l'analyse d'images)
Dans l'app : Profil → Configurer la clé API Anthropic
Obtenez votre clé sur https://console.anthropic.com

## 📱 PWA
L'app peut être installée depuis Chrome → "Ajouter à l'écran d'accueil".
Pour Google/Apple Sign-In en mode PWA, ajoutez le domaine dans Firebase.
