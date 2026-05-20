// api/gemini-vision.js — Vision avec fallback automatique Gemini → Claude
export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') { res.status(200).end(); return; }
  if (req.method !== 'POST') { res.status(405).json({ error: 'Method not allowed' }); return; }

  const { imageBase64, mimeType = 'image/jpeg', prompt } = req.body || {};
  if (!imageBase64) { res.status(400).json({ error: 'Missing imageBase64' }); return; }

  const defaultPrompt = `Analyse cette photo de frigo ou d'aliments. Liste tous les aliments visibles.
Réponds UNIQUEMENT en JSON valide sans balises markdown:
{"aliments":[{"nom":"Lait","emoji":"🥛","quantite":"1 litre","categorie":"laitage"},{"nom":"Tomates","emoji":"🍅","quantite":"4","categorie":"légumes"}]}`;

  const promptText = prompt || defaultPrompt;

  // ── 1. Essayer Gemini ───────────────────────────────────
  const GEMINI_KEY = process.env.GEMINI_API_KEY;
  if (GEMINI_KEY) {
    const MODELS = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro'];
    for (const model of MODELS) {
      try {
        const r = await fetch(
          `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${GEMINI_KEY}`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              contents: [{ parts: [
                { inline_data: { mime_type: mimeType, data: imageBase64 } },
                { text: promptText }
              ]}],
              generationConfig: { temperature: 0.1, maxOutputTokens: 1024 }
            })
          }
        );
        const data = await r.json();
        if (r.ok && data.candidates?.[0]?.content?.parts?.[0]?.text) {
          console.log(`[vision] ✅ Gemini ${model}`);
          return res.status(200).json({ text: data.candidates[0].content.parts[0].text, model });
        }
        const err = data?.error?.message || '';
        console.warn(`[vision] Gemini ${model} failed: ${err}`);
        // If quota error, stop trying Gemini models
        if (err.includes('quota') || err.includes('billing') || err.includes('exceeded')) break;
      } catch (e) {
        console.warn(`[vision] Gemini ${model} exception: ${e.message}`);
      }
    }
  }

  // ── 2. Fallback → Claude (via CLAUDE_API key) ──────────
  const CLAUDE_KEY = process.env.CLAUDE_API;
  if (CLAUDE_KEY) {
    try {
      console.log('[vision] Trying Claude fallback...');
      const r = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': CLAUDE_KEY,
          'anthropic-version': '2023-06-01',
        },
        body: JSON.stringify({
          model: 'claude-haiku-4-5-20251001',
          max_tokens: 1024,
          messages: [{
            role: 'user',
            content: [
              { type: 'image', source: { type: 'base64', media_type: mimeType, data: imageBase64 } },
              { type: 'text', text: promptText }
            ]
          }]
        })
      });
      const data = await r.json();
      if (r.ok && data.content?.[0]?.text) {
        console.log('[vision] ✅ Claude fallback OK');
        return res.status(200).json({ text: data.content[0].text, model: 'claude-haiku' });
      }
      console.warn('[vision] Claude fallback failed:', data?.error?.message);
    } catch (e) {
      console.warn('[vision] Claude fallback exception:', e.message);
    }
  }

  res.status(502).json({
    error: 'Vision non disponible',
    hint: 'Quota Gemini dépassé et pas de clé Claude. Activez la facturation sur console.cloud.google.com ou ajoutez CLAUDE_API dans Vercel.'
  });
}
