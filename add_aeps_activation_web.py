#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adds the one-time AEPS ACTIVATION page to the website (app.html).
Appends a <script id="aeps-activation-web"> block after the real-AEPS block;
adds a "First time? One-time AEPS Activation" button on the AEPS operator screen.
Needs add_real_aeps_web.py to have been applied first. Undo: restore the .bak file.

Usage:
    cd ~/Desktop/bankme-site
    python3 add_aeps_activation_web.py
"""
import sys, shutil, datetime
FILE = "app.html"
with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

if 'id="aeps-activation-web"' in content:
    print("Activation block already present - nothing to do."); sys.exit(0)
if 'id="aeps-real-web"' not in content:
    print("ERROR: the real AEPS block is missing. Run add_real_aeps_web.py first. Nothing written."); sys.exit(1)
pos = content.rfind("</body>")
tail = content[pos + len("</body>"):].strip() if pos >= 0 else None
if pos < 0 or tail.lower() != "</html>":
    print("ERROR: the last </body> is not followed only by </html>. Nothing written.")
    print("Text after the last </body>: " + repr(tail[:200] if tail is not None else None)); sys.exit(1)

JS = r'''
// ═══════════════════════════════════════════════════════════════════
// One-time AEPS (Eko Fingpay) ACTIVATION — website version.
// Same fields as the mobile AEPSActivationScreen. Rendered inside #aeps-wizard.
// ═══════════════════════════════════════════════════════════════════
var AEPS_ACT = { shops: null, states: null, files: {}, prefilled: false };

function aepsActList(r){
  var l = (r && r.d && r.d.data && r.d.data.param_attributes && r.d.data.param_attributes.list_elements) || [];
  return l.map(function(x){ return { id: String(x.value), name: String(x.label) }; })
          .filter(function(x){ return x.id && x.name && x.name !== 'Select State'; });
}
async function aepsActLoadLists(){
  async function get(path){
    try { var r = await fetch(AEPS_API + path); var j = await r.json(); return { d: j }; } catch (e) { return { d: null }; }
  }
  if (!AEPS_ACT.shops) AEPS_ACT.shops = aepsActList(await get('/eko/aeps-shop-types'));
  if (!AEPS_ACT.states) AEPS_ACT.states = aepsActList(await get('/eko/aeps-states'));
}
function aepsActOpts(list, ph){
  return '<option value="">' + ph + '</option>' + (list || []).map(function(x){ return '<option value="' + aepsEsc(x.id) + '">' + aepsEsc(x.name) + '</option>'; }).join('');
}
function aepsShrink(file){
  return new Promise(function(resolve, reject){
    var url = URL.createObjectURL(file), img = new Image();
    img.onload = function(){
      var s = Math.min(1, 1280 / Math.max(img.width, img.height));
      var c = document.createElement('canvas'); c.width = Math.round(img.width * s); c.height = Math.round(img.height * s);
      c.getContext('2d').drawImage(img, 0, 0, c.width, c.height); URL.revokeObjectURL(url);
      var q = 0.7;
      (function tryQ(){ c.toBlob(function(b){ if (b && b.size > 900 * 1024 && q > 0.3) { q -= 0.1; tryQ(); } else resolve(b); }, 'image/jpeg', q); })();
    };
    img.onerror = function(){ URL.revokeObjectURL(url); reject(new Error('That file is not a valid image')); };
    img.src = url;
  });
}
async function aepsActPick(key, input){
  var f = input.files && input.files[0]; var lab = document.getElementById('act-' + key + '-lab');
  if (!f) return;
  try {
    var b = await aepsShrink(f); AEPS_ACT.files[key] = b;
    if (lab) lab.textContent = '✅ ' + f.name + ' (' + Math.round(b.size / 1024) + ' KB)';
  } catch (e) { AEPS_ACT.files[key] = null; if (lab) lab.textContent = '❌ ' + e.message; }
}

async function aepsActivationOpen(){
  var w = document.getElementById('aeps-wizard'); if (!w) return;
  var procBtn = document.querySelector('#svc-form .btn-primary'); if (procBtn) procBtn.style.display = 'none';
  aepsBusy(1, 'Loading activation form…', 'Fetching shop types and states from Eko');
  var okId = await aepsLoadIdentity();
  await aepsActLoadLists();
  if (!okId) return aepsFail(1, 'Your account has no Eko retailer code yet. Complete retailer onboarding first.', 'initAEPSWizard()');
  AEPS_ACT.files = {}; AEPS_ACT.geo = '';
  var acc = '', ifsc = '';
  try {
    var r = await fetch(AEPS_API + '/user/' + AEPS_LIVE.opPhone + '/bank-accounts'); var j = await r.json();
    if (j && j.success && Array.isArray(j.accounts) && j.accounts.length) {
      var p = j.accounts.filter(function(a){ return a.isPrimary; })[0] || j.accounts[0];
      acc = p.accountNumber || ''; ifsc = p.ifsc || '';
    }
  } catch (e) {}
  function inp(id, label, ph, extra){ return '<label class="flabel">' + label + '</label><input class="finp" id="' + id + '" placeholder="' + (ph || '') + '" ' + (extra || '') + '/>'; }
  function addr(p, title){
    return '<div style="font-size:.72rem;font-weight:700;color:var(--muted2);text-transform:uppercase;letter-spacing:.5px;margin:6px 0">' + title + '</div>'
      + inp(p + '-line', 'Address line', 'Shop / door no, street, area')
      + inp(p + '-city', 'City', 'City')
      + '<label class="flabel">State</label><select class="fsel" id="' + p + '-state">' + aepsActOpts(AEPS_ACT.states, '-- Select State --') + '</select>'
      + inp(p + '-pin', 'Pincode', '6-digit pincode', 'type="tel" maxlength="6" oninput="this.value=this.value.replace(/[^0-9]/g,\'\')"');
  }
  function file(key, label){
    return '<label class="flabel">' + label + '</label>'
      + '<input type="file" accept="image/*" id="act-' + key + '" onchange="aepsActPick(\'' + key + '\',this)" style="width:100%;margin-bottom:4px;font-size:.78rem;color:var(--muted2)"/>'
      + '<div id="act-' + key + '-lab" style="font-size:.72rem;color:var(--muted2);margin-bottom:10px">No file chosen</div>';
  }
  w.innerHTML =
    '<div style="background:rgba(245,158,11,.07);border:1px solid rgba(245,158,11,.28);border-radius:11px;padding:12px;margin-bottom:14px">'
    + '<div style="font-weight:700;color:var(--gold);font-size:.9rem;margin-bottom:4px">🔐 One-time AEPS Activation</div>'
    + '<div style="font-size:.74rem;color:var(--muted2);line-height:1.55">Do this once per retailer. Your PAN and Aadhaar photos go to Eko for KYC. Eko may take time to approve; until approved, AEPS transactions will be declined.</div></div>'
    + '<div style="font-size:.78rem;color:var(--muted2);margin-bottom:10px">Retailer: <strong style="color:var(--text)">' + aepsEsc(CU ? CU.name : '') + '</strong> · Eko code ' + aepsEsc(AEPS_LIVE.userCode) + '</div>'
    + inp('act-account', 'Bank Account Number', 'Account number', 'type="tel" value="' + aepsEsc(acc) + '"')
    + inp('act-ifsc', 'IFSC Code', 'e.g. HDFC0001234', 'maxlength="11" style="text-transform:uppercase" value="' + aepsEsc(ifsc) + '"')
    + '<datalist id="act-devs">' + AEPS_DEVICES.map(function(d){ return '<option value="' + aepsEsc(d.label) + '">'; }).join('') + '</datalist>'
    + inp('act-model', 'Biometric Device Model', 'e.g. Morpho MSO 1300 E3 L1', 'list="act-devs"')
    + inp('act-serial', 'Device Serial Number', 'Printed on the device')
    + inp('act-aadhaar', 'Your Aadhaar Number', '12-digit Aadhaar', 'type="tel" maxlength="12" style="letter-spacing:3px;font-weight:600" oninput="this.value=this.value.replace(/[^0-9]/g,\'\')"')
    + '<label class="flabel">Shop Type</label><select class="fsel" id="act-shop">' + aepsActOpts(AEPS_ACT.shops, '-- Select Shop Type --') + '</select>'
    + addr('act-off', 'Office / shop address')
    + '<label style="display:flex;align-items:center;gap:8px;font-size:.78rem;color:var(--muted2);margin:4px 0 10px"><input type="checkbox" id="act-same" checked onchange="document.getElementById(\'act-proof-box\').style.display=this.checked?\'none\':\'block\'"/> Address as per proof is same as office</label>'
    + '<div id="act-proof-box" style="display:none">' + addr('act-prf', 'Address as per proof') + '</div>'
    + '<label class="flabel">Shop GPS Location</label>'
    + '<button type="button" onclick="aepsActGeo()" class="btn-primary" style="background:var(--bg3);color:var(--text);border:1px solid var(--border2);margin-bottom:4px">📍 Capture my current location</button>'
    + '<div id="act-geo-lab" style="font-size:.72rem;color:var(--muted2);margin-bottom:10px">Not captured (be at the shop)</div>'
    + file('pan', 'PAN Card photo') + file('front', 'Aadhaar — front photo') + file('back', 'Aadhaar — back photo')
    + '<button onclick="aepsActSubmit()" class="btn-primary" id="act-submit">Submit Activation to Eko →</button>'
    + '<button onclick="initAEPSWizard()" style="width:100%;margin-top:8px;padding:10px;border-radius:10px;background:transparent;border:1px solid var(--border);color:var(--muted2);cursor:pointer;font-size:.82rem">← Back</button>';
}

async function aepsActGeo(){
  var lab = document.getElementById('act-geo-lab'); if (lab) lab.textContent = 'Getting location…';
  AEPS_ACT.geo = (await aepsGeo()) || '';
  if (lab) lab.textContent = AEPS_ACT.geo ? '✅ ' + AEPS_ACT.geo : '❌ Could not get location — allow it for this site and retry';
}

function aepsActVal(id){ var e = document.getElementById(id); return e ? String(e.value || '').trim() : ''; }
function aepsActCollect(){
  var same = document.getElementById('act-same').checked;
  var pre = same ? 'act-off' : 'act-prf';
  function stateOf(p){ var s = document.getElementById(p + '-state'); return { id: s.value, name: s.value ? s.options[s.selectedIndex].text : '' }; }
  var o = stateOf('act-off'), pr = stateOf(pre);
  return {
    account: aepsActVal('act-account'), ifsc: aepsActVal('act-ifsc').toUpperCase(),
    model: aepsActVal('act-model'), serial: aepsActVal('act-serial'), aadhaar: aepsActVal('act-aadhaar'),
    shop: aepsActVal('act-shop'),
    off: { line: aepsActVal('act-off-line'), city: aepsActVal('act-off-city'), state: o, pin: aepsActVal('act-off-pin') },
    prf: { line: aepsActVal(pre + '-line'), city: aepsActVal(pre + '-city'), state: pr, pin: aepsActVal(pre + '-pin') }
  };
}
function aepsActValidate(v){
  if (!/^\d{9,18}$/.test(v.account)) return 'Enter a valid bank account number';
  if (!/^[A-Z]{4}0[A-Z0-9]{6}$/.test(v.ifsc)) return 'Enter a valid 11-character IFSC (e.g. HDFC0001234)';
  if (!v.model || !v.serial) return 'Device model and serial number are required';
  if (!/^\d{12}$/.test(v.aadhaar)) return 'Enter a valid 12-digit Aadhaar number';
  if (!v.shop) return 'Select a shop type';
  var blocks = [['Office', v.off], ['Proof', v.prf]];
  for (var i = 0; i < blocks.length; i++) {
    var b = blocks[i][1];
    if (!b.line || !b.city || !b.state.id || !/^\d{6}$/.test(b.pin)) return blocks[i][0] + ' address is incomplete (line, city, state, 6-digit pincode)';
  }
  if (!AEPS_ACT.geo) return 'Capture the shop GPS location';
  if (!AEPS_ACT.files.pan || !AEPS_ACT.files.front || !AEPS_ACT.files.back) return 'PAN, Aadhaar front and Aadhaar back photos are all required';
  return '';
}

async function aepsActSubmit(){
  var v = aepsActCollect(), err = aepsActValidate(v);
  if (err) { toast(err, 'e'); return; }
  var btn = document.getElementById('act-submit'); if (btn) { btn.disabled = true; btn.textContent = 'Submitting…'; }
  var f = new FormData();
  f.append('modelname', v.model); f.append('devicenumber', v.serial);
  f.append('account', v.account); f.append('ifsc', v.ifsc);
  f.append('shop_type', v.shop); f.append('aadhar', v.aadhaar); f.append('latlong', AEPS_ACT.geo);
  f.append('office_line', v.off.line); f.append('office_city', v.off.city); f.append('office_state', v.off.state.name);
  f.append('office_state_id', v.off.state.id); f.append('office_pincode', v.off.pin);
  f.append('proof_line', v.prf.line); f.append('proof_city', v.prf.city); f.append('proof_state', v.prf.state.name);
  f.append('proof_state_id', v.prf.state.id); f.append('proof_pincode', v.prf.pin);
  f.append('pan_card', AEPS_ACT.files.pan, 'pan.jpg');
  f.append('aadhar_front', AEPS_ACT.files.front, 'aadhar_front.jpg');
  f.append('aadhar_back', AEPS_ACT.files.back, 'aadhar_back.jpg');
  var c = new AbortController(), t = setTimeout(function(){ c.abort(); }, 90000);
  try {
    var r = await fetch(AEPS_API + '/eko/agent/' + encodeURIComponent(AEPS_LIVE.userCode) + '/aeps-fingpay/activate', { method: 'PUT', body: f, signal: c.signal });
    var j = await r.json();
    var d = j && j.data ? j.data : null;
    var ok = j && j.success && (!d || d.status === 0 || d.status === undefined);
    var msg = (d && d.message) || (typeof j.error === 'string' ? j.error : (j.error && j.error.message)) || '';
    AEPS_ACT.files = {};
    if (ok) {
      var w = document.getElementById('aeps-wizard');
      w.innerHTML = '<div style="background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.35);border-radius:14px;padding:20px;text-align:center;margin-bottom:14px">'
        + '<div style="font-size:2.5rem;margin-bottom:8px">✅</div><div style="font-weight:700;color:var(--green);font-size:1rem;margin-bottom:6px">Activation submitted to Eko</div>'
        + '<div style="font-size:.78rem;color:var(--muted2);line-height:1.55">' + aepsEsc(msg || 'Eko will review and approve your AEPS service.') + ' Once approved, start AEPS and verify your fingerprint.</div></div>'
        + '<button onclick="initAEPSWizard()" class="btn-primary">Go to AEPS →</button>';
      toast('AEPS activation submitted ✅', 's');
    } else {
      aepsFail(1, msg || 'Activation was not accepted. Check the details and try again.', 'aepsActivationOpen()');
    }
  } catch (e) {
    aepsFail(1, e.name === 'AbortError' ? 'Server is slow to respond — wait a minute and check before resubmitting.' : 'Network error: ' + e.message, 'aepsActivationOpen()');
  } finally { clearTimeout(t); }
}

// Add an "Activate AEPS" entry on the operator screen (Step 1)
(function(){
  var orig = renderAEPSStep1;
  renderAEPSStep1 = async function(){
    await orig();
    var w = document.getElementById('aeps-wizard');
    if (w && w.querySelector('#op-aadhaar') && !w.querySelector('#aeps-act-entry')) {
      w.insertAdjacentHTML('beforeend',
        '<button id="aeps-act-entry" onclick="aepsActivationOpen()" style="width:100%;margin-top:12px;padding:11px;border-radius:10px;background:rgba(37,99,235,.08);border:1px solid rgba(37,99,235,.3);color:#2563eb;cursor:pointer;font-size:.8rem;font-weight:700">🔐 First time? One-time AEPS Activation</button>');
    }
  };
})();
'''
BLOCK = '<script id="aeps-activation-web">' + JS + '</script>\n</body>'

backup = FILE + ".bak." + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
shutil.copy(FILE, backup)
content = content[:pos] + BLOCK + content[pos + len("</body>"):]
with open(FILE, "w", encoding="utf-8") as f:
    f.write(content)
print("OK: AEPS Activation page added to " + FILE)
print("    Backup: " + backup)
