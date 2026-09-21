export const config = {
  runtime: 'nodejs',
  regions: ['bom1'], // Mumbai region
};

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { path, body } = req.body;

  try {
    const targetUrl = path.startsWith('http') ? path : 'https://in.staging.decentro.tech/' + path;
    const response = await fetch(targetUrl, {
      method: 'POST',
      headers: {
        'client_id': req.headers['client_id'],
        'client_secret': req.headers['client_secret'],
        'module_secret': req.headers['module_secret'] || '',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    const data = await response.json();
    res.status(response.status).json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}
