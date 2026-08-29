// ============================================================
// BankMe OTP Worker — Cloudflare Worker with KV Storage
// PayPe Technologies
// ============================================================

const MSG91_AUTH_KEY    = '6a205aa31603beca8502b342';
const MSG91_TEMPLATE_ID = '1207178039509109431';
const MSG91_SENDER_ID   = 'PAYPE';
const OTP_EXPIRY_SEC    = 600; // 10 minutes

// Generate 6-digit OTP
function generateOTP() {
  return String(Math.floor(100000 + Math.random() * 900000));
}

// CORS headers
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Content-Type': 'application/json'
};

// Send SMS via MSG91 - let MSG91 generate OTP internally
async function sendSMS(phone, otp) {
  // Use MSG91 flow API which sends OTP to any number
  const url = `https://api.msg91.com/api/v5/flow/`;
  
  const payload = JSON.stringify({
    template_id: MSG91_TEMPLATE_ID,
    sender: MSG91_SENDER_ID,
    short_url: '0',
    mobiles: '91' + phone,
    VAR: otp
  });

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'authkey': MSG91_AUTH_KEY,
      'Content-Type': 'application/JSON'
    },
    body: payload
  });
  return await response.json();
}

// Send Email via MSG91
async function sendEmail(email, otp, name) {
  const customerName = name || 'Customer';
  const emailBody = `
  <div style="font-family:sans-serif;background:#0a0e1a;padding:32px;border-radius:12px;max-width:480px;margin:0 auto">
    <div style="text-align:center;margin-bottom:24px">
      <div style="font-size:1.8rem;font-weight:800;color:#00d4aa">🏦 BankMe</div>
      <div style="color:#888;font-size:.82rem;margin-top:4px">Powered by PayPe Technologies</div>
    </div>
    <p style="color:#ccc;margin-bottom:6px">Dear ${customerName},</p>
    <p style="color:#aaa;margin-bottom:20px">Your One-Time Password (OTP) for BankMe login is:</p>
    <div style="background:#1a2035;border:1px solid rgba(0,212,170,.3);border-radius:12px;padding:28px;text-align:center;margin-bottom:20px">
      <div style="font-size:2.6rem;font-weight:900;letter-spacing:12px;color:#00d4aa">${otp}</div>
      <div style="color:#666;font-size:.82rem;margin-top:10px">Valid for 10 minutes only</div>
    </div>
    <div style="background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.2);border-radius:8px;padding:12px;margin-bottom:20px">
      <p style="color:#f87171;font-size:.82rem;margin:0">Do NOT share this OTP with anyone.</p>
    </div>
    <hr style="border:none;border-top:1px solid #1e2a3a;margin:20px 0"/>
    <div style="text-align:center">
      <div style="color:#00d4aa;font-weight:700;margin-bottom:4px">BankMe · www.bankme.co.in</div>
      <div style="color:#555;font-size:.72rem">PayPe Technologies Pvt Ltd · +91 99448 57191</div>
    </div>
  </div>`;

  const payload = JSON.stringify({
    to: [{ name: customerName, email: email }],
    from: { name: 'BankMe by PayPe Technologies', email: 'noreply@bankme.co.in' },
    domain: 'bankme.co.in',
    mail_type_id: '1',
    subject: `Your BankMe OTP: ${otp}`,
    body: emailBody
  });

  const response = await fetch('https://api.msg91.com/api/v5/email/send', {
    method: 'POST',
    headers: {
      'authkey': MSG91_AUTH_KEY,
      'Content-Type': 'application/json'
    },
    body: payload
  });
  return await response.json();
}

export default {
  async fetch(request, env, ctx) {

    // Handle preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    const url    = new URL(request.url);
    const action = url.searchParams.get('action');
    const phone  = url.searchParams.get('phone');
    const email  = url.searchParams.get('email');
    const name   = url.searchParams.get('name') || 'Customer';

    // ── SEND / RESEND OTP ──
    if (action === 'send' || action === 'resend') {

      const hasPhone = phone && /^[6-9]\d{9}$/.test(phone);
      const hasEmail = email && /\S+@\S+\.\S+/.test(email);

      if (!hasPhone && !hasEmail) {
        return new Response(JSON.stringify({
          type: 'error', message: 'Valid phone or email required'
        }), { headers: corsHeaders });
      }

      // Generate OTP in worker
      const otp = generateOTP();
      const key = 'otp_' + (phone || email.replace(/[@.]/g, '_'));

      // Store in KV with expiry
      await env.OTP_KV.put(key, JSON.stringify({
        otp,
        expiry: Date.now() + (OTP_EXPIRY_SEC * 1000)
      }), { expirationTtl: OTP_EXPIRY_SEC });

      let smsSent   = false;
      let emailSent = false;
      let errors    = [];

      // Send SMS
      if (hasPhone) {
        try {
          const smsResult = await sendSMS(phone, otp);
          console.log('SMS result:', JSON.stringify(smsResult));
          smsSent = smsResult && (smsResult.type === 'success' || smsResult.message === 'Request submitted successfully');
          if (!smsSent) errors.push('SMS: ' + (smsResult.message || JSON.stringify(smsResult)));
        } catch(e) {
          errors.push('SMS error: ' + e.message);
          console.log('SMS error:', e.message);
        }
      }

      // Send Email
      if (hasEmail) {
        try {
          const emailResult = await sendEmail(email, otp, name);
          console.log('Email result:', JSON.stringify(emailResult));
          emailSent = true;
        } catch(e) {
          errors.push('Email error: ' + e.message);
        }
      }

      if (smsSent || emailSent) {
        return new Response(JSON.stringify({
          type: 'success',
          message: 'OTP sent successfully',
          sms: smsSent,
          email: emailSent
        }), { headers: corsHeaders });
      } else {
        return new Response(JSON.stringify({
          type: 'error',
          message: 'Failed to send OTP',
          errors: errors
        }), { headers: corsHeaders });
      }
    }

    // ── VERIFY OTP ──
    if (action === 'verify') {
      const enteredOtp = url.searchParams.get('otp');
      const key        = 'otp_' + (phone || (email && email.replace(/[@.]/g, '_')));

      if (!key || !enteredOtp) {
        return new Response(JSON.stringify({
          type: 'error', message: 'Phone/email and OTP required'
        }), { headers: corsHeaders });
      }

      // Get from KV
      const stored = await env.OTP_KV.get(key, { type: 'json' });

      if (!stored) {
        return new Response(JSON.stringify({
          type: 'error', message: 'OTP expired or not found. Please request a new OTP.'
        }), { headers: corsHeaders });
      }

      if (Date.now() > stored.expiry) {
        await env.OTP_KV.delete(key);
        return new Response(JSON.stringify({
          type: 'error', message: 'OTP expired. Please request a new OTP.'
        }), { headers: corsHeaders });
      }

      if (enteredOtp !== stored.otp) {
        return new Response(JSON.stringify({
          type: 'error', message: 'Invalid OTP. Please try again.'
        }), { headers: corsHeaders });
      }

      // Verified — delete from KV
      await env.OTP_KV.delete(key);

      return new Response(JSON.stringify({
        type: 'success', message: 'OTP verified successfully.'
      }), { headers: corsHeaders });
    }

    // Default
    return new Response(JSON.stringify({
      type: 'error',
      message: 'Invalid action. Use: send, verify, resend'
    }), { status: 400, headers: corsHeaders });
  }
};
