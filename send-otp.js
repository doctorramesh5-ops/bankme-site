// ============================================================
// BankMe OTP Proxy — Netlify Function
// PayPe Technologies
// ============================================================

const MSG91_AUTH_KEY    = '6a205aa31603beca8502b342';
const MSG91_TEMPLATE_ID = '1207178039509109431';
const MSG91_SENDER_ID   = 'PAYPE';

exports.handler = async function(event, context) {

  // Only allow POST
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: JSON.stringify({ success: false, message: 'Method not allowed' }) };
  }

  // CORS headers
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Content-Type': 'application/json'
  };

  // Handle preflight
  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 200, headers, body: '' };
  }

  let input;
  try {
    input = JSON.parse(event.body);
  } catch(e) {
    return { statusCode: 400, headers, body: JSON.stringify({ success: false, message: 'Invalid request' }) };
  }

  const { type, otp, mobile, email, name } = input;

  // Validate OTP
  if (!otp || !/^\d{6}$/.test(otp)) {
    return { statusCode: 400, headers, body: JSON.stringify({ success: false, message: 'Invalid OTP' }) };
  }

  // ── SMS OTP ──
  if (type === 'sms') {
    if (!mobile || !/^[6-9]\d{9}$/.test(mobile)) {
      return { statusCode: 400, headers, body: JSON.stringify({ success: false, message: 'Invalid mobile number' }) };
    }

    const message = `Dear Customer, Your OTP for login is ${otp} . This OTP is valid for 10 minutes. Please do not share this OTP with anyone. - PayPe Technologies.`;

    const url = `https://api.msg91.com/api/v5/otp?authkey=${MSG91_AUTH_KEY}&mobile=91${mobile}&message=${encodeURIComponent(message)}&sender=${MSG91_SENDER_ID}&otp=${otp}&template_id=${MSG91_TEMPLATE_ID}&otp_expiry=10`;

    try {
      const response = await fetch(url);
      const data = await response.json();

      if (data && data.type === 'success') {
        return { statusCode: 200, headers, body: JSON.stringify({ success: true, message: 'OTP sent successfully' }) };
      } else {
        return { statusCode: 200, headers, body: JSON.stringify({ success: false, message: data.message || 'SMS failed' }) };
      }
    } catch(e) {
      return { statusCode: 500, headers, body: JSON.stringify({ success: false, message: 'SMS gateway error' }) };
    }
  }

  // ── Email OTP ──
  if (type === 'email') {
    if (!email || !/\S+@\S+\.\S+/.test(email)) {
      return { statusCode: 400, headers, body: JSON.stringify({ success: false, message: 'Invalid email' }) };
    }

    const customerName = name || 'Customer';
    const emailBody = `
      <div style="font-family:sans-serif;background:#0a0e1a;padding:32px;border-radius:12px;max-width:480px;margin:0 auto">
        <div style="text-align:center;margin-bottom:24px">
          <div style="font-size:1.6rem;font-weight:800;color:#00d4aa">🏦 BankMe</div>
          <div style="color:#888;font-size:.85rem">Powered by PayPe Technologies</div>
        </div>
        <p style="color:#ccc;margin-bottom:8px">Dear ${customerName},</p>
        <p style="color:#aaa;margin-bottom:20px">Your One-Time Password (OTP) for BankMe login is:</p>
        <div style="background:#1a2035;border:1px solid #00d4aa33;border-radius:10px;padding:24px;text-align:center;margin-bottom:20px">
          <div style="font-size:2.4rem;font-weight:900;letter-spacing:10px;color:#00d4aa">${otp}</div>
          <div style="color:#666;font-size:.82rem;margin-top:8px">Valid for 10 minutes only</div>
        </div>
        <p style="color:#888;font-size:.82rem">⚠️ Do not share this OTP with anyone. BankMe will never ask for your OTP.</p>
        <hr style="border:none;border-top:1px solid #222;margin:20px 0"/>
        <p style="color:#555;font-size:.75rem;text-align:center">
          PayPe Technologies Pvt Ltd | www.bankme.co.in<br/>
          +91 99448 57191 | itsupport@paype.co.in
        </p>
      </div>`;

    const payload = JSON.stringify({
      to: [{ name: customerName, email: email }],
      from: { name: 'BankMe by PayPe Technologies', email: 'noreply@bankme.co.in' },
      domain: 'bankme.co.in',
      mail_type_id: '1',
      subject: `Your BankMe OTP: ${otp}`,
      body: emailBody
    });

    try {
      const response = await fetch('https://api.msg91.com/api/v5/email/send', {
        method: 'POST',
        headers: {
          'authkey': MSG91_AUTH_KEY,
          'Content-Type': 'application/json'
        },
        body: payload
      });
      return { statusCode: 200, headers, body: JSON.stringify({ success: true, message: 'Email OTP sent' }) };
    } catch(e) {
      return { statusCode: 500, headers, body: JSON.stringify({ success: false, message: 'Email gateway error' }) };
    }
  }

  return { statusCode: 400, headers, body: JSON.stringify({ success: false, message: 'Invalid type' }) };
};
