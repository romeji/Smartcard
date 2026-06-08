# Déploiement GitHub

1. Créer un dépôt GitHub.
2. Pousser ce projet.
3. Si utilisation de Vercel :
   - Importer le dépôt dans Vercel.
   - Configurer les variables d'environnement :
     - ALLOWED_ORIGIN
     - APP_BASE_URL
     - GOOGLE_CLIENT_ID
     - GOOGLE_CLIENT_SECRET
     - STRIPE_SECRET_KEY
     - STRIPE_WEBHOOK_SECRET
4. Déployer.

Le workflow GitHub Pages est présent mais les routes API nécessitent Vercel ou un environnement Node compatible.
