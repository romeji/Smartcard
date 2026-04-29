// api/claude.js — Proxy Vercel pour l'API Claude
// La clé est stockée dans la variable d'environnement CLAUDE_API (Vercel Dashboard)
// Elle n'est JAMAIS exposée au navigateur

export default async function handler(req, res) {
  // CORS pour votre domaine Vercel
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if(req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if(req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const apiKey = process.env.CLAUDE_API;
  if(!apiKey) {
    return res.status(500).json({ error: 'CLAUDE_API environment variable not set' });
  }

  try {
    const body = req.body;

    // Forcer le bon modèle si absent
    if(!body.model) body.model = 'claude-sonnet-4-20250514';
    if(!body.max_tokens) body.max_tokens = 1000;

    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify(body)
    });

    const data = await response.json();

    if(!response.ok) {
      return res.status(response.status).json(data);
    }

    return res.status(200).json(data);

  } catch(err) {
    console.error('Claude proxy error:', err);
    return res.status(500).json({ error: err.message });
  }
}
