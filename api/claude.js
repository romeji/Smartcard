// api/claude.js — Claude + fallback GPT-4o-mini
export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if(req.method === 'OPTIONS') { res.status(200).end(); return; }
  if(req.method !== 'POST')    { res.status(405).json({error:'Method not allowed'}); return; }

  const body = req.body || {};
  if(!body.model)      body.model      = 'claude-3-5-haiku-20241022';
  if(!body.max_tokens) body.max_tokens = 1024;

  const claudeKey = process.env.CLAUDE_API;
  const openaiKey = process.env.OPENAI_API;

  // Log keys presence (not values) for debugging
  console.log('Keys present — Claude:', !!claudeKey, '| OpenAI:', !!openaiKey);

  // ── 1. Essayer Claude ──────────────────────────────────
  if(claudeKey) {
    try {
      const r = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': claudeKey,
          'anthropic-version': '2023-06-01',
        },
        body: JSON.stringify(body),
      });
      const data = await r.json();
      if(r.ok) {
        console.log('Claude OK');
        return res.status(200).json(data);
      }
      const errMsg = data?.error?.message || '';
      console.warn('Claude error:', r.status, errMsg);
      // Ne tomber sur OpenAI que si c'est un problème de crédit/auth
      const isCreditError = errMsg.includes('credit') || errMsg.includes('balance') || r.status === 400 || r.status === 402;
      if(!isCreditError) {
        return res.status(r.status).json(data);
      }
      console.log('Credit exhausted, trying OpenAI...');
    } catch(e) {
      console.warn('Claude fetch failed:', e.message);
    }
  }

  // ── 2. Fallback GPT-4o-mini ──────────────────────────────
  if(!openaiKey) {
    console.error('No OPENAI_API key set in Vercel env vars');
    return res.status(500).json({ error: 'Crédit Claude épuisé et aucune clé OpenAI configurée. Ajoutez OPENAI_API dans Vercel → Settings → Environment Variables.' });
  }

  try {
    console.log('Calling OpenAI gpt-4o-mini...');
    const messages = [];
    if(body.system) messages.push({ role: 'system', content: body.system });
    (body.messages || []).forEach(m => messages.push({ role: m.role, content: m.content }));

    const r = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + openaiKey,
      },
      body: JSON.stringify({
        model: 'gpt-4o-mini',
        messages,
        max_tokens: body.max_tokens || 1024,
        temperature: 0.3,
      }),
    });

    const data = await r.json();
    if(!r.ok) {
      console.error('OpenAI error:', r.status, data?.error?.message);
      return res.status(r.status).json({ error: data?.error?.message || 'OpenAI error' });
    }

    const text = data.choices?.[0]?.message?.content || '';
    console.log('OpenAI OK, text length:', text.length);

    // Réponse au format Anthropic pour compatibilité frontend
    return res.status(200).json({
      content: [{ type: 'text', text }],
      model: 'gpt-4o-mini',
      _provider: 'openai',
    });

  } catch(e) {
    console.error('OpenAI fallback error:', e.message);
    return res.status(500).json({ error: 'OpenAI: ' + e.message });
  }
}
