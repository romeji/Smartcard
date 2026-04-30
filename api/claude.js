// api/claude.js — Vercel serverless function
// Proxies Claude API calls using CLAUDE_API env var

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if(req.method === 'OPTIONS') { res.status(200).end(); return; }
  if(req.method !== 'POST') { res.status(405).json({error: 'Method not allowed'}); return; }

  const apiKey = process.env.CLAUDE_API;
  if(!apiKey) { 
    console.error('CLAUDE_API env var not set');
    res.status(500).json({error: 'CLAUDE_API not configured'}); 
    return; 
  }

  try {
    const body = req.body;
    if(!body.model) body.model = 'claude-3-5-haiku-20241022';
    if(!body.max_tokens) body.max_tokens = 1024;

    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    if(!response.ok) console.error('Anthropic error:', response.status, data?.error?.message);
    res.status(response.status).json(data);
  } catch(e) {
    console.error('Proxy error:', e.message);
    res.status(500).json({error: e.message});
  }
}
