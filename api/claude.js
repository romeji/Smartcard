// api/claude.js — Proxy avec fallback GPT-4o-mini si Claude échoue
// Variables d'environnement Vercel : CLAUDE_API et OPENAI_API

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if(req.method === 'OPTIONS') { res.status(200).end(); return; }
  if(req.method !== 'POST')    { res.status(405).json({error:'Method not allowed'}); return; }

  const body = req.body || {};
  if(!body.model)      body.model      = 'claude-3-5-haiku-20241022';
  if(!body.max_tokens) body.max_tokens = 1024;

  // ── 1. Essayer Claude ──────────────────────────────────────
  const claudeKey = process.env.CLAUDE_API;
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
      // Succès OU erreur non liée au crédit → retourner tel quel
      if(r.ok || (data?.error?.type !== 'authentication_error' && !data?.error?.message?.includes('credit'))) {
        return res.status(r.status).json(data);
      }
      console.warn('Claude credit exhausted, falling back to OpenAI');
    } catch(e) {
      console.warn('Claude failed:', e.message, '— trying OpenAI');
    }
  }

  // ── 2. Fallback GPT-4o-mini ────────────────────────────────
  const openaiKey = process.env.OPENAI_API;
  if(!openaiKey) {
    return res.status(500).json({ error: 'No API key available. Set CLAUDE_API or OPENAI_API in Vercel env vars.' });
  }

  try {
    // Convertir le format Anthropic → OpenAI
    const messages = [];
    if(body.system) messages.push({ role: 'system', content: body.system });
    (body.messages || []).forEach(m => messages.push({ role: m.role, content: m.content }));

    const r = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${openaiKey}`,
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

    // Convertir la réponse OpenAI → format Anthropic (pour que le frontend marche sans changement)
    const text = data.choices?.[0]?.message?.content || '';
    return res.status(200).json({
      content: [{ type: 'text', text }],
      model: 'gpt-4o-mini',
      _provider: 'openai',
    });

  } catch(e) {
    console.error('OpenAI fallback error:', e.message);
    return res.status(500).json({ error: e.message });
  }
}
