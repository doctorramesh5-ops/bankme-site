/* BankMe Kuberan website assistant. Guests: public answers only. Signed-in users: own account via login token. */
(function () {
  if (window.__kbw) return; window.__kbw = 1;
  var API = 'https://bankme-backend.onrender.com';
  var BASE = (document.currentScript && document.currentScript.src) ? document.currentScript.src.replace(/[^\/]*$/, '') : '/';
  var ICON = BASE + 'kuberan-bot.png';
  var S = { hist: [], busy: false, rec: null, signed: false };
  function tok() { try { return localStorage.getItem('bankme_token') || ''; } catch (e) { return ''; } }
  function $(id) { return document.getElementById(id); }
  var css = '#kbwBtn{position:fixed;right:16px;bottom:16px;z-index:99990;width:62px;height:62px;border-radius:50%;border:0;background:#0d2540 url(' + ICON + ') center/46px no-repeat;box-shadow:0 6px 22px rgba(0,0,0,.45),0 0 0 2px rgba(245,184,46,.7);cursor:pointer}' +
    '#kbwBtn:hover{transform:scale(1.05)}' +
    '#kbwBtn small{position:absolute;right:70px;bottom:18px;background:#0d2540;color:#f5e9c8;border:1px solid #2a4a6b;padding:5px 10px;border-radius:99px;white-space:nowrap;font:12px system-ui,sans-serif}' +
    '#kbwP{position:fixed;right:16px;bottom:90px;z-index:99991;width:370px;max-width:calc(100vw - 24px);height:540px;max-height:calc(100vh - 110px);background:#0b1a2b;color:#e8eef5;border:1px solid #2a4a6b;border-radius:16px;display:flex;flex-direction:column;overflow:hidden;box-shadow:0 14px 40px rgba(0,0,0,.5);font:14px system-ui,-apple-system,sans-serif}' +
    '#kbwP.kbwh{display:none}' +
    '#kbwP .kh{display:flex;align-items:center;gap:8px;padding:10px 12px;background:#0d2540;border-bottom:1px solid #2a4a6b}' +
    '#kbwP .kh img{width:34px;height:34px}#kbwP .kh b{display:block;font-size:14px}#kbwP .kh small{color:#9db3c8;font-size:11px}#kbwP .sp{flex:1}' +
    '#kbwP select{background:#0b1a2b;color:#e8eef5;border:1px solid #2a4a6b;border-radius:8px;padding:3px 4px;font-size:12px;max-width:92px}' +
    '#kbwP .kx{background:transparent;border:0;color:#9db3c8;cursor:pointer;font-size:20px;padding:0 6px}' +
    '#kbwM{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px}' +
    '.kbm{max-width:86%;padding:8px 12px;border-radius:12px;white-space:pre-wrap;word-break:break-word;font-size:13.5px;line-height:1.45}' +
    '.kbm.bot{background:#12263c;border:1px solid #2a4a6b;align-self:flex-start}.kbm.me{background:linear-gradient(90deg,#f5b82e,#ffd777);color:#1a1200;align-self:flex-end}.kbm.ty{color:#9db3c8;font-style:italic}' +
    '#kbwC{display:flex;gap:6px;flex-wrap:wrap;padding:0 12px 8px}#kbwC button{background:transparent;border:1px solid #2a4a6b;color:#9db3c8;border-radius:99px;padding:4px 10px;font-size:12px;cursor:pointer}#kbwC button:hover{border-color:#f5b82e;color:#fff}' +
    '#kbwN{font-size:10.5px;color:#7f97ad;padding:0 12px 6px}' +
    '#kbwF{display:flex;gap:6px;padding:10px;border-top:1px solid #2a4a6b}#kbwF input{flex:1;min-width:0;background:#0b1a2b;color:#e8eef5;border:1px solid #2a4a6b;border-radius:10px;padding:9px 10px;font-size:14px}' +
    '#kbwF button{border:0;border-radius:10px;padding:0 12px;cursor:pointer;font-weight:600}#kbwSend{background:#f5b82e;color:#1a1200}#kbwMic{background:#12263c;color:#e8eef5;border:1px solid #2a4a6b!important;font-size:16px}#kbwMic.rec{background:#c0392b;animation:kbwp 1s infinite}' +
    '@keyframes kbwp{50%{opacity:.5}}' +
    '@media(max-width:520px){#kbwP{right:8px;bottom:84px;width:calc(100vw - 16px);height:calc(100vh - 100px)}}';
  var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);

  function add(role, text, cls) {
    var d = document.createElement('div'); d.className = 'kbm ' + (role === 'user' ? 'me' : 'bot') + (cls ? ' ' + cls : ''); d.textContent = text;
    $('kbwM').appendChild(d); $('kbwM').scrollTop = $('kbwM').scrollHeight; return d;
  }
  function notice(t) { var n = $('kbwN'); if (n) n.textContent = t; }
  async function post(path, body, token) {
    var h = { 'Content-Type': 'application/json' }; if (token) h['Authorization'] = 'Bearer ' + token;
    var r = await fetch(API + path, { method: 'POST', headers: h, body: JSON.stringify(body) });
    var j = null; try { j = await r.json(); } catch (e) {}
    return { status: r.status, j: j };
  }
  async function send(text) {
    text = String(text || '').trim(); if (!text || S.busy) return;
    S.busy = true; $('kbwI').value = ''; $('kbwC').style.display = 'none';
    add('user', text); var ty = add('bot', 'Kuberan is typing…', 'ty');
    var body = { message: text, lang: $('kbwL').value, history: S.hist.slice(-10) };
    var t = tok(), res;
    try {
      res = t ? await post('/kuberan/chat', body, t) : await post('/kuberan/public', body);
      if (t && (res.status === 401 || res.status === 403)) { S.signed = false; notice('Your login expired. Please sign in again to see your own account. Answering as a guest.'); res = await post('/kuberan/public', body); }
    } catch (e) { res = { status: 0, j: null }; }
    ty.remove(); S.busy = false;
    var j = res.j;
    var reply = (j && j.success && j.reply) ? j.reply : ((j && j.message) || 'Kuberan could not answer right now. Please try again or email support@bankme.co.in.');
    add('bot', reply);
    if (j && j.success) { S.hist.push({ role: 'user', content: text }); S.hist.push({ role: 'assistant', content: reply }); S.hist = S.hist.slice(-10); }
  }
  async function voiceUp(blob) {
    try {
      var t = tok(); var h = { 'Content-Type': blob.type || 'audio/webm' }; if (t) h['Authorization'] = 'Bearer ' + t;
      var q = '?lang=' + encodeURIComponent($('kbwL').value);
      var r = await fetch(API + (t ? '/kuberan/voice' : '/kuberan/public-voice') + q, { method: 'POST', headers: h, body: blob });
      if (t && (r.status === 401 || r.status === 403)) { delete h['Authorization']; r = await fetch(API + '/kuberan/public-voice' + q, { method: 'POST', headers: h, body: blob }); }
      return await r.json();
    } catch (e) { return { success: false, message: 'Cannot reach the server.' }; }
  }
  async function mic() {
    if (S.rec) { try { S.rec.stop(); } catch (e) {} return; }
    if (!navigator.mediaDevices || !window.MediaRecorder) { notice('Voice typing is not supported in this browser.'); return; }
    var stream; try { stream = await navigator.mediaDevices.getUserMedia({ audio: true }); } catch (e) { notice('Please allow the microphone to use voice.'); return; }
    var mt = ''; ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg;codecs=opus'].some(function (x) { if (MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(x)) { mt = x; return true; } return false; });
    var rec = mt ? new MediaRecorder(stream, { mimeType: mt }) : new MediaRecorder(stream), chunks = [];
    S.rec = rec; $('kbwMic').classList.add('rec'); $('kbwI').placeholder = 'Listening… tap the mic to stop';
    rec.ondataavailable = function (e) { if (e.data && e.data.size) chunks.push(e.data); };
    var timer = setTimeout(function () { try { rec.stop(); } catch (e) {} }, 28000);
    rec.onstop = async function () {
      clearTimeout(timer); stream.getTracks().forEach(function (x) { x.stop(); }); S.rec = null;
      var m = $('kbwMic'), inp = $('kbwI'); if (!m || !inp) return; m.classList.remove('rec');
      var blob = new Blob(chunks, { type: rec.mimeType || mt || 'audio/webm' });
      if (blob.size < 800) { inp.placeholder = 'Type your question'; notice('I did not catch that. Please try again.'); return; }
      inp.placeholder = 'Understanding your voice…';
      var r = await voiceUp(blob); inp = $('kbwI'); if (!inp) return; inp.placeholder = 'Type your question';
      if (r && r.success && r.text) { inp.value = r.text; inp.focus(); } else notice((r && r.message) || 'Could not understand. Please type.');
    };
    rec.start();
  }
  function build() {
    var p = document.createElement('div'); p.id = 'kbwP';
    var img = document.createElement('img'); img.alt = ''; img.src = ICON;
    p.innerHTML = '<div class="kh"><span id="kbwIc"></span><div><b>BankMe Kuberan</b><small id="kbwSub"></small></div><span class="sp"></span><select id="kbwL" title="Language"><option value="">Auto</option><option value="en">English</option><option value="hi">हिन्दी</option><option value="ta">தமிழ்</option><option value="te">తెలుగు</option><option value="kn">ಕನ್ನಡ</option><option value="ml">മലയാളം</option><option value="mr">मराठी</option><option value="bn">বাংলা</option><option value="gu">ગુજરાતી</option><option value="pa">ਪੰਜਾਬੀ</option></select><button class="kx" id="kbwX" aria-label="Close">&times;</button></div>' +
      '<div id="kbwM"></div><div id="kbwC"></div><div id="kbwN"></div><form id="kbwF"><button type="button" id="kbwMic" aria-label="Voice typing">🎤</button><input id="kbwI" maxlength="500" placeholder="Type your question" autocomplete="off"><button type="submit" id="kbwSend">Send</button></form>';
    document.body.appendChild(p);
    $('kbwIc').appendChild(img); $('kbwIc').style.display = 'flex';
    img.style.cssText = 'width:34px;height:34px';
    $('kbwX').onclick = function () { p.classList.add('kbwh'); };
    $('kbwF').onsubmit = function (e) { e.preventDefault(); send($('kbwI').value); };
    $('kbwMic').onclick = mic;
    S.signed = !!tok();
    $('kbwSub').textContent = S.signed ? 'Signed in: ask about your account' : 'Guest: general help';
    notice(S.signed ? 'Never share OTP, PIN, full Aadhaar or PAN with anyone, including Kuberan.' : 'Guest mode cannot see accounts. Sign in to the app for your own KYC, transactions and charges. Never share OTP or PIN.');
    add('bot', S.signed ? 'Namaste! I am Kuberan. Ask me about your KYC, transactions, wallet, charges or commission.' : 'Namaste! I am Kuberan, the BankMe assistant. Ask me about BankMe services, sign-up and how things work. For your own account details, please sign in.');
    var chips = S.signed ? ['Is my KYC done?', 'Show my last transactions', 'My wallet balance', 'AEPS charges'] : ['What services does BankMe offer?', 'How do I sign up?', 'How does KYC work?', 'Talk to support'];
    chips.forEach(function (c) { var x = document.createElement('button'); x.type = 'button'; x.textContent = c; x.onclick = function () { send(c === 'Talk to support' ? 'How can I contact BankMe support?' : c); }; $('kbwC').appendChild(x); });
    /* KBW_SIGNIN */ if (!S.signed) { var si = document.createElement('button'); si.type = 'button'; si.textContent = 'Sign in to see my account'; si.style.cssText = 'border-color:#f5b82e;color:#f5b82e'; si.onclick = function () { window.location.href = 'app.html'; }; $('kbwC').appendChild(si); }
  }
  function mount() {
    var b = document.createElement('button'); b.id = 'kbwBtn'; b.setAttribute('aria-label', 'Ask Kuberan'); b.innerHTML = '<small>Ask Kuberan</small>'; document.body.appendChild(b);
    b.onclick = function () {
      var p = $('kbwP');
      if (!p) { build(); $('kbwI').focus(); return; }
      var wasHidden = p.classList.contains('kbwh');
      p.classList.toggle('kbwh');
      if (wasHidden && !!tok() !== S.signed) { p.remove(); S.hist = []; build(); }
    };
  }
  if (document.body) mount(); else document.addEventListener('DOMContentLoaded', mount);
})();
