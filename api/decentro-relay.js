export const config = {
  runtime: 'nodejs',
  regions: ['bom1'], // Mumbai region
};

export default async function handler(req, res) {
  try {
    if (req.method === 'GET') {
      const { path } = req.query;
      const targetUrl = path.startsWith('http') ? path : 'https://in.staging.decentro.tech/' + path;
      const response = await fetch(targetUrl, {
        method: 'GET',
        headers: {
          'client_id': req.headers['client_id'],
          'client_secret': req.headers['client_secret'],
        },
      });
      const data = await response.json();
      return res.status(response.status).json(data);
    }

    if (req.method !== 'POST') {
      return res.status(405).json({ error: 'Method not allowed' });
    }

    const { path, body, headers: customHeaders } = req.body;
    const targetUrl = path.startsWith('http') ? path : 'https://in.staging.decentro.tech/' + path;

    // If customHeaders provided, forward those exactly (generic passthrough mode)
    // Otherwise, fall back to original Decentro-specific headers for backward compatibility
    const forwardHeaders = customHeaders || {
      'client_id': req.headers['client_id'],
      'client_secret': req.headers['client_secret'],
      'module_secret': req.headers['module_secret'] || '',
      'Content-Type': 'application/json',
    };

    const response = await fetch(targetUrl, {
      method: 'POST',
      headers: forwardHeaders,
      body: JSON.stringify(body),
    });
    const data = await response.json();
    res.status(response.status).json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}
