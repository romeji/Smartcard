// api/gemini-vision.js — Gemini Vision pour reconnaissance photo frigo
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
Liste tous les aliments visibles.
Réponds UNIQUEMENT en JSON valide sans balises markdown:
{"aliments":[{"nom":"Lait","emoji":"🥛","quantite":"1 litre","categorie":"laitage"}]}`;

  const payload = {
    contents: [{ parts: [
      { inline_data: { mime_type: mimeType, data: imageBase64 } },
      { text: prompt || defaultPrompt }
    ]}],
    generationConfig: { temperature: 0.1, maxOutputTokens: 1024 }
  };

  // Liste des modèles à essayer dans l'ordre
  const MODELS = [
    'gemini-2.0-flash-lite',
    'gemini-2.0-flash',
    'gemini-1.5-flash',
    'gemini-1.5-pro',
  ];

  const errors = [];
  for (const model of MODELS) {
    try {
      const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${GEMINI_API_KEY}`;
      console.log(`[gemini-vision] Trying ${model}...`);
      const r = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await r.json();
      if (r.ok && data.candidates?.[0]?.content?.parts?.[0]?.text) {
        const text = data.candidates[0].content.parts[0].text;
        console.log(`[gemini-vision] ✅ ${model} OK`);
        return res.status(200).json({ text, model });
      }
      const errMsg = data?.error?.message || `HTTP ${r.status}`;
      console.warn(`[gemini-vision] ❌ ${model}: ${errMsg}`);
      errors.push(`${model}: ${errMsg}`);
    } catch (e) {
      console.warn(`[gemini-vision] ❌ ${model} exception: ${e.message}`);
      errors.push(`${model}: ${e.message}`);
    }
  }

  // Tous les modèles ont échoué — renvoyer le détail
  res.status(502).json({
    error: 'Tous les modèles Gemini ont échoué',
    details: errors,
    hint: 'Vérifiez que GEMINI_API_KEY est valide et que les modèles sont activés sur https://aistudio.google.com'
  });
}
