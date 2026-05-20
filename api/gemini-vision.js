// api/gemini-vision.js — Gemini Vision pour reconnaissance photo frigo
// Runtime: Node.js (pas Edge) pour accès à process.env
// Variable requise : GEMINI_API_KEY dans Vercel Dashboard > Settings > Environment Variables

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') { res.status(200).end(); return; }
  if (req.method !== 'POST') { res.status(405).json({ error: 'Method not allowed' }); return; }

  const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
  if (!GEMINI_API_KEY) {
    res.status(500).json({ error: 'GEMINI_API_KEY not configured in Vercel environment variables' });
    return;
  }

  const { imageBase64, mimeType = 'image/jpeg', prompt } = req.body || {};

  if (!imageBase64) {
    res.status(400).json({ error: 'Missing imageBase64' });
    return;
  }

  const defaultPrompt = `Analyse cette photo de frigo ou d'aliments.
Liste tous les aliments visibles en JSON.
Pour chaque aliment: nom en français, emoji adapté, quantité estimée, catégorie.
Réponds UNIQUEMENT en JSON valide sans balises markdown:
{"aliments":[{"nom":"Lait","emoji":"🥛","quantite":"1 litre","categorie":"laitage"},{"nom":"Tomates","emoji":"🍅","quantite":"4","categorie":"légumes"}]}`;

  const geminiPayload = {
    contents: [{
      parts: [
        { inline_data: { mime_type: mimeType, data: imageBase64 } },
        { text: prompt || defaultPrompt }
      ]
    }],
    generationConfig: {
      temperature: 0.1,
      maxOutputTokens: 1024,
    }
  };

  try {
    const geminiRes = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${GEMINI_API_KEY}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(geminiPayload),
      }
    );

    if (!geminiRes.ok) {
      const errText = await geminiRes.text();
      res.status(502).json({ error: 'Gemini API error', details: errText });
      return;
    }

    const geminiData = await geminiRes.json();
    const text = geminiData.candidates?.[0]?.content?.parts?.[0]?.text || '';
    res.status(200).json({ text, raw: geminiData });

  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}
