export const config = {
  runtime: 'nodejs',
  regions: ['bom1'], // Mumbai region
};

// RELAY_KYC_PROD_V1: KYC calls (Aadhaar/DigiLocker etc.) use Decentro production; everything else stays on staging until tested.
// Set DECENTRO_KYC_ENV=staging in the host settings to switch KYC back to staging instantly.
function decentroBase(p) {
  const kyc = /^v2\/kyc\//.test(String(p || ''));
  const env = String(process.env.DECENTRO_KYC_ENV || 'production').toLowerCase();
  return (kyc && env !== 'staging') ? 'https://in.decentro.tech/' : 'https://in.staging.decentro.tech/';
}

export default async function handler(req, res) {
  try {
    if (req.method === 'GET') {
      const { path } = req.query;
      const targetUrl = path.startsWith('http') ? path : decentroBase(path) + path;
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
    const targetUrl = path.startsWith('http') ? path : decentroBase(path) + path;

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
