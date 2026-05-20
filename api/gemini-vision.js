// api/gemini-vision.js — Gemini Vision pour reconnaissance photo frigo
// Runtime: Node.js — Variable requise : GEMINI_API_KEY dans Vercel

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') { res.status(200).end(); return; }
  if (req.method !== 'POST') { res.status(405).json({ error: 'Method not allowed' }); return; }

  const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
  if (!GEMINI_API_KEY) {
    res.status(500).json({ error: 'GEMINI_API_KEY not configured' });
    return;
  }

  const { imageBase64, mimeType = 'image/jpeg', prompt } = req.body || {};
  if (!imageBase64) { res.status(400).json({ error: 'Missing imageBase64' }); return; }

  const defaultPrompt = `Analyse cette photo de frigo ou d'aliments.
Liste tous les aliments visibles en JSON.
Réponds UNIQUEMENT en JSON valide sans balises markdown:
{"aliments":[{"nom":"Lait","emoji":"🥛","quantite":"1 litre","categorie":"laitage"},{"nom":"Tomates","emoji":"🍅","quantite":"4","categorie":"légumes"}]}`;

  // Try models in order: gemini-2.0-flash (latest) → gemini-1.5-flash-latest → gemini-pro-vision
  const MODELS = [
    'gemini-2.0-flash',
    'gemini-1.5-flash-latest',
    'gemini-1.5-flash-8b',
    'gemini-pro-vision',
  ];

  const payload = {
    contents: [{ parts: [
      { inline_data: { mime_type: mimeType, data: imageBase64 } },
      { text: prompt || defaultPrompt }
    ]}],
    generationConfig: { temperature: 0.1, maxOutputTokens: 1024 }
  };

  let lastError = '';
  for (const model of MODELS) {
    try {
      const r = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${GEMINI_API_KEY}`,
        { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }
      );
      const data = await r.json();
      if (r.ok) {
        const text = data.candidates?.[0]?.content?.parts?.[0]?.text || '';
        console.log(`[gemini-vision] OK avec ${model}`);
        return res.status(200).json({ text, model });
      }
      lastError = data?.error?.message || `HTTP ${r.status}`;
      console.warn(`[gemini-vision] ${model} failed:`, lastError);
      // If not a 404/model-not-found error, stop trying
      if (r.status !== 404 && r.status !== 400) break;
    } catch (e) {
      lastError = e.message;
      console.warn(`[gemini-vision] ${model} exception:`, e.message);
    }
  }

  res.status(502).json({ error: 'Tous les modèles Gemini ont échoué', details: lastError });
}
