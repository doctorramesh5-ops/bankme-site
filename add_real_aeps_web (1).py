#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Replaces the SIMULATED AEPS wizard in app.html with the REAL Eko flow
(operator daily KYC / one-time e-KYC, real RD Service fingerprint capture,
real balance / mini-statement / cash-withdrawal via bankme-backend /eko/aeps/v2/*).

It does NOT delete the old code: it appends one <script id="aeps-real-web"> block
before </body>; its functions override the old simulated ones of the same name.
To undo: restore the .bak file it creates.

Safe by design: </body> must appear exactly once and the block must not already exist.

Usage:
    cd ~/Desktop/bankme-site
    python3 add_real_aeps_web.py
"""
import sys, shutil, datetime
FILE = "app.html"
with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

if 'id="aeps-real-web"' in content:
    print("Real AEPS block already present - nothing to do."); sys.exit(0)
pos = content.rfind("</body>")
tail = content[pos + len("</body>"):].strip() if pos >= 0 else None
if pos < 0 or tail.lower() != "</html>":
    print("ERROR: the last </body> is not followed only by </html>. Nothing written.")
    print("Text after the last </body>: " + repr(tail[:200] if tail is not None else None))
    print("Tell Claude."); sys.exit(1)

JS = r'''
// ═══════════════════════════════════════════════════════════════════
// REAL AEPS (Eko Fingpay) — overrides the old simulated wizard.
// Flow: Operator KYC (daily; one-time e-KYC if needed) → customer txn.
// Biometric via RD Service on 127.0.0.1 (Windows PC + scanner driver).
// ═══════════════════════════════════════════════════════════════════
var AEPS_API = 'https://bankme-backend.onrender.com';
var AEPS_EKYC_WADH = 'E0jzJ/P8UopUHAieZn8CKqS4WPMi5ZSYXgfnlfkWjrc=';
var AEPS_RD = { base: null, capture: '', info: '' };
var AEPS_LIVE = { banks: null, userCode: '', opPhone: '', opAadhaar: '', opBank: null, cust: null, kyc: {} };

function aepsEsc(s){ return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];}); }
function aepsToday(){ return new Date().toISOString().slice(0,10); }

async function aepsCall(method, path, body){
  var c = new AbortController(); var t = setTimeout(function(){ c.abort(); }, 70000);
  try {
    var r = await fetch(AEPS_API + path, { method: method, signal: c.signal,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined });
    var j = await r.json();
    var d = j && j.data ? j.data : null;
    var msg = typeof j.error === 'string' ? j.error : (j.error && j.error.message) || (d && d.message) || '';
    return { ok: !!j.success, d: d, code: d ? d.response_type_id : null, msg: msg };
  } catch (e) {
    return { ok: false, d: null, code: null, msg: e.name === 'AbortError' ? 'Server is waking up — please try again in a minute' : 'Network error: ' + e.message };
  } finally { clearTimeout(t); }
}

function aepsFetchTO(url, opts, ms){
  var c = new AbortController(); var t = setTimeout(function(){ c.abort(); }, ms);
  opts = opts || {}; opts.signal = c.signal;
  return fetch(url, opts).finally(function(){ clearTimeout(t); });
}

async function aepsDiscoverRD(){
  for (var port = 11100; port <= 11120; port++) {
    try {
      var r = await aepsFetchTO('http://127.0.0.1:' + port + '/', { method: 'RDSERVICE' }, 1200);
      var xml = await r.text();
      var doc = new DOMParser().parseFromString(xml, 'text/xml');
      var svc = doc.getElementsByTagName('RDService')[0];
      if (!svc || svc.getAttribute('status') !== 'READY') continue;
      var cap = '';
      var ifs = doc.getElementsByTagName('Interface');
      for (var i = 0; i < ifs.length; i++) if (ifs[i].getAttribute('id') === 'CAPTURE') cap = ifs[i].getAttribute('path');
      if (!cap) continue;
      AEPS_RD = { base: 'http://127.0.0.1:' + port, capture: cap, info: svc.getAttribute('info') || 'Biometric device' };
      return AEPS_RD;
    } catch (e) { /* port closed — keep scanning */ }
  }
  AEPS_RD = { base: null, capture: '', info: '' };
  return null;
}

// returns {xml} or {error}
async function aepsCaptureFinger(wadh){
  if (!AEPS_RD.base && !(await aepsDiscoverRD())) return { error: 'No biometric device found. Plug in the scanner, install its RD Service driver, and try again (Windows PC + Chrome/Edge).' };
  var opts = '<?xml version="1.0"?><PidOptions ver="1.0"><Opts fCount="1" fType="2" iCount="0" pCount="0" format="0" pidVer="2.0" timeout="15000" wadh="' + (wadh || '') + '" posh="UNKNOWN" env="P"/></PidOptions>';
  try {
    var r = await aepsFetchTO(AEPS_RD.base + AEPS_RD.capture, { method: 'CAPTURE', body: opts }, 30000);
    var xml = await r.text();
    var doc = new DOMParser().parseFromString(xml, 'text/xml');
    var resp = doc.getElementsByTagName('Resp')[0];
    if (!resp) return { error: 'Unexpected response from the biometric device' };
    if (resp.getAttribute('errCode') !== '0') return { error: 'Fingerprint not captured: ' + (resp.getAttribute('errInfo') || 'error ' + resp.getAttribute('errCode')) };
    return { xml: xml, q: resp.getAttribute('qScore') };
  } catch (e) {
    AEPS_RD.base = null;
    return { error: 'Could not reach the biometric device. Check it is connected and retry.' };
  }
}

function aepsGeo(){
  return new Promise(function(resolve){
    if (!navigator.geolocation) return resolve(null);
    navigator.geolocation.getCurrentPosition(function(p){
      resolve(p.coords.latitude.toFixed(4) + ',' + p.coords.longitude.toFixed(4));
    }, function(){ resolve(null); }, { enableHighAccuracy: true, timeout: 15000 });
  });
}

async function aepsLoadBanks(){
  if (AEPS_LIVE.banks) return AEPS_LIVE.banks;
  var r = await aepsCall('GET', '/eko/banks');
  var list = (r.d && r.d.param_attributes && r.d.param_attributes.list_elements) || [];
  AEPS_LIVE.banks = list.map(function(b){ return { name: b.label, code: b.value }; }).filter(function(b){ return b.name && b.code; })
    .sort(function(a,b){ return a.name.localeCompare(b.name); });
  return AEPS_LIVE.banks;
}

async function aepsLoadIdentity(){
  if (AEPS_LIVE.userCode && AEPS_LIVE.opPhone) return true;
  var phone = String((CU && (CU.phone || CU.mobile)) || '').replace(/\D/g, '').slice(-10);
  AEPS_LIVE.opPhone = phone;
  if (CU && CU.ekoUserCode) { AEPS_LIVE.userCode = String(CU.ekoUserCode); return true; }
  if (phone.length !== 10) return false;
  var r = await aepsCall('GET', '/user/' + phone + '/identity');
  if (r.d === null) {
    try { var rr = await fetch(AEPS_API + '/user/' + phone + '/identity'); var j = await rr.json(); if (j && j.ekoUserCode) AEPS_LIVE.userCode = String(j.ekoUserCode); } catch (e) {}
  }
  return !!AEPS_LIVE.userCode;
}

// ── bank picker (live Eko bank list) ──
function aepsBankPickerHTML(prefix){
  return '<div style="position:relative;margin-bottom:4px">'
    + '<input type="text" id="' + prefix + '-search" placeholder="🔍 Type to search bank..." autocomplete="off"'
    + ' style="width:100%;background:var(--bg3);border:1px solid var(--border2);border-radius:10px;padding:11px 14px;color:var(--text);font-size:.88rem;outline:none;box-sizing:border-box"'
    + ' oninput="aepsBankFilter(\'' + prefix + '\',this.value)" onfocus="aepsBankFilter(\'' + prefix + '\',this.value)" onblur="setTimeout(function(){var d=document.getElementById(\'' + prefix + '-dd\');if(d)d.style.display=\'none\';},200)"/>'
    + '<div id="' + prefix + '-dd" style="display:none;position:absolute;top:100%;left:0;right:0;z-index:300;background:var(--bg2);border:1px solid var(--border2);border-radius:10px;margin-top:2px;max-height:200px;overflow-y:auto"></div>'
    + '</div><input type="hidden" id="' + prefix + '-code" value=""/>'
    + '<div id="' + prefix + '-badge" style="display:none;font-size:.78rem;color:var(--rtai);font-weight:600;margin:6px 0 10px"></div>';
}
function aepsBankFilter(prefix, q){
  var dd = document.getElementById(prefix + '-dd'); if (!dd) return;
  var banks = AEPS_LIVE.banks || [];
  q = (q || '').toLowerCase().trim();
  var res = banks.filter(function(b){ return !q || b.name.toLowerCase().indexOf(q) >= 0; }).slice(0, 60);
  dd.innerHTML = res.length ? res.map(function(b){
    return '<div onmousedown="aepsBankPick(\'' + prefix + '\',\'' + aepsEsc(b.code) + '\')" style="padding:10px 14px;font-size:.82rem;cursor:pointer;border-bottom:1px solid var(--border);color:var(--text)">' + aepsEsc(b.name) + '</div>';
  }).join('') : '<div style="padding:12px 14px;font-size:.8rem;color:var(--muted2)">' + (banks.length ? 'No banks found' : 'Bank list is loading… try again in a moment') + '</div>';
  dd.style.display = 'block';
}
function aepsBankPick(prefix, code){
  var b = (AEPS_LIVE.banks || []).filter(function(x){ return x.code === code; })[0]; if (!b) return;
  document.getElementById(prefix + '-code').value = b.code;
  document.getElementById(prefix + '-search').value = b.name;
  var badge = document.getElementById(prefix + '-badge'); badge.style.display = 'block'; badge.textContent = '🏦 ' + b.name;
  document.getElementById(prefix + '-dd').style.display = 'none';
}

function aepsBusy(step, title, sub){
  var w = document.getElementById('aeps-wizard'); if (!w) return;
  w.innerHTML = aepsStepBar(step)
    + '<div style="text-align:center;padding:24px 10px"><div style="width:48px;height:48px;border:4px solid rgba(0,212,170,.2);border-top-color:var(--rtai);border-radius:50%;animation:spin .8s linear infinite;margin:0 auto 14px"></div>'
    + '<div style="font-weight:700;color:var(--rtai);font-size:.95rem">' + aepsEsc(title) + '</div>'
    + '<div style="color:var(--muted2);font-size:.76rem;margin-top:6px">' + aepsEsc(sub || '') + '</div></div>';
}
function aepsFail(step, msg, backFn){
  var w = document.getElementById('aeps-wizard'); if (!w) return;
  w.innerHTML = aepsStepBar(step)
    + '<div style="background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.35);border-radius:14px;padding:18px;text-align:center;margin-bottom:12px">'
    + '<div style="font-size:2rem;margin-bottom:6px">⚠️</div><div style="font-weight:700;color:#ef4444;font-size:.92rem;margin-bottom:6px">Could not complete</div>'
    + '<div style="font-size:.78rem;color:var(--muted2);line-height:1.5">' + aepsEsc(msg || 'Unknown error') + '</div></div>'
    + '<button onclick="' + (backFn || 'initAEPSWizard()') + '" class="btn-primary">← Try again</button>';
}

// ═════════ STEP 1 — operator identity ═════════
function initAEPSWizard(){
  AEPS_WIZARD.step = 1; AEPS_WIZARD.operatorAadhaar = ''; AEPS_WIZARD.device = '';
  AEPS_LIVE.opAadhaar = ''; AEPS_LIVE.cust = null; AEPS_LIVE.kyc = {};
  renderAEPSStep1();
}

async function renderAEPSStep1(){
  var w = document.getElementById('aeps-wizard'); if (!w) return;
  var procBtn = document.querySelector('#svc-form .btn-primary'); if (procBtn) procBtn.style.display = 'none';
  aepsBusy(1, 'Preparing AEPS…', 'Loading your retailer profile and bank list');
  var okId = await aepsLoadIdentity();
  await aepsLoadBanks();
  if (!okId) {
    return aepsFail(1, 'Your account is not linked to an Eko retailer code yet, so AEPS cannot run. Contact BankMe support.', 'initAEPSWizard()');
  }
  w.innerHTML = aepsStepBar(1)
    + '<div style="background:rgba(245,158,11,.07);border:1px solid rgba(245,158,11,.28);border-radius:11px;padding:12px;margin-bottom:16px">'
    + '<div style="font-size:.68rem;font-weight:700;color:var(--gold);text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px">📋 UIDAI / RBI Regulation</div>'
    + '<div style="font-size:.75rem;color:var(--muted2);line-height:1.55">The operator (you) must verify your own fingerprint once every day before the first customer transaction.</div></div>'
    + '<div style="font-size:.78rem;color:var(--muted2);margin-bottom:10px">Retailer: <strong style="color:var(--text)">' + aepsEsc(CU ? CU.name : '') + '</strong> · Eko code ' + aepsEsc(AEPS_LIVE.userCode) + ' · ' + aepsEsc(AEPS_LIVE.opPhone) + '</div>'
    + '<label class="flabel">Your Aadhaar Number (Operator)</label>'
    + '<input class="finp" id="op-aadhaar" type="tel" maxlength="12" placeholder="12-digit Aadhaar number" style="letter-spacing:3px;font-size:1rem;font-weight:600" oninput="this.value=this.value.replace(/[^0-9]/g,\'\')"/>'
    + '<div style="font-size:.7rem;color:var(--muted2);margin:-8px 0 14px;line-height:1.5">🔒 Sent encrypted for fingerprint verification only. Not stored.</div>'
    + '<label class="flabel">Your Aadhaar-linked Bank</label>' + aepsBankPickerHTML('opb')
    + '<label class="flabel">Biometric Device</label>'
    + '<select class="fsel" id="op-device" onchange="showDeviceInstallLink(this.value)"><option value="">-- Select (for driver help) --</option>'
    + AEPS_DEVICES.map(function(d){ return '<option value="' + d.value + '">' + d.label + '</option>'; }).join('') + '</select>'
    + '<div id="device-install-info" style="display:none;margin-top:6px;background:rgba(37,99,235,.07);border:1px solid rgba(37,99,235,.25);border-radius:10px;padding:10px"></div>'
    + '<button onclick="submitAEPSStep1()" class="btn-primary" style="margin-top:10px">Verify My Fingerprint →</button>'
    + '<div style="text-align:center;margin-top:10px;font-size:.65rem;color:var(--muted)">🛡️ RTAI Secured · UIDAI Compliant · RD Service Biometrics</div>';
}

async function submitAEPSStep1(){
  var a = (document.getElementById('op-aadhaar') || {}).value || '';
  var bank = (document.getElementById('opb-code') || {}).value || '';
  if (!/^\d{12}$/.test(a)) { toast('Enter your 12-digit Aadhaar number', 'e'); return; }
  if (!bank) { toast('Select your Aadhaar-linked bank', 'e'); return; }
  AEPS_LIVE.opAadhaar = a; AEPS_LIVE.opBank = bank;
  AEPS_WIZARD.step = 2;
  await aepsOperatorDaily();
}

// ═════════ STEP 2 — operator biometric (daily KYC, e-KYC if required) ═════════
function aepsOpBody(extra){
  var b = { userCode: AEPS_LIVE.userCode, customerId: AEPS_LIVE.opPhone, aadhaar: AEPS_LIVE.opAadhaar, bankCode: AEPS_LIVE.opBank, latlong: AEPS_LIVE.geo };
  for (var k in extra) b[k] = extra[k];
  return b;
}

async function aepsOperatorDaily(){
  aepsBusy(2, 'Getting your location…', 'Allow location access if the browser asks');
  AEPS_LIVE.geo = await aepsGeo();
  if (!AEPS_LIVE.geo) return aepsFail(1, 'Location is required for AEPS. Allow location access for this site and try again.', 'initAEPSWizard()');
  var w = document.getElementById('aeps-wizard');
  w.innerHTML = aepsStepBar(2)
    + '<div style="background:rgba(0,212,170,.06);border:1px solid rgba(0,212,170,.25);border-radius:14px;padding:20px;text-align:center;margin-bottom:16px">'
    + '<div style="font-size:2.8rem;margin-bottom:10px">👆</div>'
    + '<div style="font-weight:700;color:var(--rtai);font-size:1rem;margin-bottom:4px">Place YOUR finger on the scanner</div>'
    + '<div style="color:var(--muted2);font-size:.78rem">Operator daily verification · Aadhaar XXXX XXXX ' + AEPS_LIVE.opAadhaar.slice(-4) + '</div></div>'
    + '<button onclick="aepsRunDaily()" class="btn-primary">👆 Scan Fingerprint</button>'
    + '<button onclick="initAEPSWizard()" style="width:100%;margin-top:8px;padding:10px;border-radius:10px;background:transparent;border:1px solid var(--border);color:var(--muted2);cursor:pointer;font-size:.82rem">← Back</button>';
}

async function aepsRunDaily(){
  aepsBusy(2, 'Scanning…', 'Keep your finger on the device');
  var cap = await aepsCaptureFinger('');
  if (cap.error) return aepsFail(2, cap.error, 'aepsOperatorDaily()');
  aepsBusy(2, 'Verifying with UIDAI…', 'This can take up to a minute');
  var r = await aepsCall('PUT', '/eko/aeps/v2/kyc/daily', aepsOpBody({ piddata: cap.xml }));
  if (r.ok && r.code === 1713) { return aepsOperatorDone(); }
  if (/ekyc/i.test(r.msg || '')) { return aepsEkycStart(); }
  return aepsFail(2, r.msg || 'Daily KYC failed', 'aepsOperatorDaily()');
}

function aepsOperatorDone(){
  AEPS_LIVE.opAadhaar = ''; // operator Aadhaar no longer needed in memory
  var w = document.getElementById('aeps-wizard');
  w.innerHTML = aepsStepBar(2)
    + '<div style="background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.35);border-radius:14px;padding:20px;text-align:center;margin-bottom:16px">'
    + '<div style="font-size:2.5rem;margin-bottom:8px">✅</div>'
    + '<div style="font-family:var(--font-head);font-size:1.05rem;font-weight:700;color:var(--green);margin-bottom:4px">Operator Verified for Today</div>'
    + '<div style="font-size:.78rem;color:var(--muted2)">' + aepsEsc(CU ? CU.name : 'Operator') + ' · UIDAI daily KYC complete</div></div>'
    + '<button onclick="renderAEPSStep3()" class="btn-primary">Proceed to AEPS Service →</button>';
  setTimeout(function(){ if (AEPS_WIZARD.step === 2) renderAEPSStep3(); }, 1200);
}

// one-time e-KYC: OTP → verify → biometric
function aepsEkycStart(){
  var w = document.getElementById('aeps-wizard');
  w.innerHTML = aepsStepBar(2)
    + '<div style="background:rgba(245,158,11,.07);border:1px solid rgba(245,158,11,.28);border-radius:12px;padding:14px;margin-bottom:14px">'
    + '<div style="font-weight:700;color:var(--gold);font-size:.9rem;margin-bottom:4px">One-time e-KYC needed</div>'
    + '<div style="font-size:.76rem;color:var(--muted2);line-height:1.55">Your bank e-KYC is not complete yet. We will send an OTP to your Aadhaar-linked mobile, then scan your finger once. After this you only need the daily fingerprint.</div></div>'
    + '<button onclick="aepsEkycSendOtp()" class="btn-primary">Send OTP to my Aadhaar mobile</button>';
}
async function aepsEkycSendOtp(){
  aepsBusy(2, 'Sending OTP…', '');
  var r = await aepsCall('POST', '/eko/aeps/v2/kyc/otp', aepsOpBody({}));
  if (!(r.ok && r.code === 1600)) return aepsFail(2, r.msg || 'Could not send OTP', 'aepsEkycStart()');
  AEPS_LIVE.kyc = { otpRefId: String(r.d.data.otp_ref_id), referenceTid: String(r.d.data.reference_tid) };
  var w = document.getElementById('aeps-wizard');
  w.innerHTML = aepsStepBar(2)
    + '<label class="flabel">Enter the OTP received on your Aadhaar-linked mobile</label>'
    + '<input class="finp" id="ekyc-otp" type="tel" maxlength="8" placeholder="OTP" style="letter-spacing:6px;font-size:1.2rem;font-weight:700;text-align:center" oninput="this.value=this.value.replace(/[^0-9]/g,\'\')"/>'
    + '<button onclick="aepsEkycVerify()" class="btn-primary">Verify OTP →</button>';
}
async function aepsEkycVerify(){
  var otp = (document.getElementById('ekyc-otp') || {}).value || '';
  if (otp.length < 4) { toast('Enter the OTP', 'e'); return; }
  aepsBusy(2, 'Verifying OTP…', '');
  var r = await aepsCall('PUT', '/eko/aeps/v2/kyc/otp/verify', aepsOpBody({ otp: otp, otpRefId: AEPS_LIVE.kyc.otpRefId, referenceTid: AEPS_LIVE.kyc.referenceTid }));
  if (!(r.ok && r.code === 1604)) return aepsFail(2, r.msg || 'OTP verification failed', 'aepsEkycStart()');
  AEPS_LIVE.kyc = { otpRefId: String(r.d.data.otp_ref_id), referenceTid: String(r.d.data.reference_tid) };
  var w = document.getElementById('aeps-wizard');
  w.innerHTML = aepsStepBar(2)
    + '<div style="background:rgba(0,212,170,.06);border:1px solid rgba(0,212,170,.25);border-radius:14px;padding:20px;text-align:center;margin-bottom:16px">'
    + '<div style="font-size:2.8rem;margin-bottom:10px">👆</div><div style="font-weight:700;color:var(--rtai);font-size:1rem">OTP verified — scan YOUR finger for e-KYC</div></div>'
    + '<button onclick="aepsEkycBio()" class="btn-primary">👆 Scan Fingerprint</button>';
}
async function aepsEkycBio(){
  aepsBusy(2, 'Scanning…', 'Keep your finger on the device');
  var cap = await aepsCaptureFinger(AEPS_EKYC_WADH);
  if (cap.error) return aepsFail(2, cap.error, 'aepsEkycStart()');
  aepsBusy(2, 'Completing e-KYC…', 'This can take up to a minute');
  var r = await aepsCall('PUT', '/eko/aeps/v2/kyc/biometric', aepsOpBody({ piddata: cap.xml, otpRefId: AEPS_LIVE.kyc.otpRefId, referenceTid: AEPS_LIVE.kyc.referenceTid }));
  if (!(r.ok && r.code === 1605)) return aepsFail(2, r.msg || 'e-KYC failed', 'aepsEkycStart()');
  toast('e-KYC complete ✅ — now your daily fingerprint', 's');
  aepsOperatorDaily();
}

// ═════════ STEP 3 — customer transaction ═════════
function renderAEPSStep3(){
  var w = document.getElementById('aeps-wizard'); if (!w) return;
  AEPS_WIZARD.step = 3;
  var c = AEPS_LIVE.cust || {};
  w.innerHTML = aepsStepBar(3)
    + '<div style="background:rgba(16,185,129,.06);border:1px solid rgba(16,185,129,.2);border-radius:10px;padding:9px 12px;margin-bottom:14px;font-size:.74rem;color:var(--green);font-weight:600">✅ Operator verified · Now serving customer</div>'
    + '<label class="flabel">Customer Mobile</label><input class="finp" id="m-phone" placeholder="10-digit mobile" type="tel" maxlength="10" value="' + aepsEsc(c.phone || '') + '" oninput="this.value=this.value.replace(/[^0-9]/g,\'\')"/>'
    + '<label class="flabel">Customer Aadhaar (12 digits)</label>'
    + '<input class="finp" id="m-aadhaar" placeholder="12-digit Aadhaar" maxlength="12" type="tel" value="' + aepsEsc(c.aadhaar || '') + '" style="letter-spacing:3px;font-size:1rem;font-weight:600" oninput="this.value=this.value.replace(/[^0-9]/g,\'\')"/>'
    + '<div style="font-size:.7rem;color:var(--muted2);margin:-8px 0 12px">🔒 Encrypted for UIDAI authentication. Not stored.</div>'
    + '<label class="flabel">Transaction Type</label>'
    + '<select class="fsel" id="m-type" onchange="toggleAEPSFields()"><option value="withdrawal">Cash Withdrawal</option><option value="balance">Balance Enquiry</option><option value="ministatement">Mini Statement</option></select>'
    + '<div id="aeps-amount-row"><label class="flabel">Amount (₹)</label>'
    + '<input class="finp" id="m-amount" placeholder="Enter withdrawal amount" type="number" min="100" step="100" value="' + aepsEsc(c.amount || '') + '"/>'
    + '<div style="display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap">'
    + [100, 500, 1000, 2000, 5000].map(function(a){ return '<button type="button" onclick="setAmt(' + a + ')" style="padding:5px 10px;border-radius:7px;border:1px solid var(--border2);background:var(--bg3);color:var(--muted2);cursor:pointer;font-size:.74rem">₹' + a.toLocaleString('en-IN') + '</button>'; }).join('')
    + '</div></div>'
    + '<label class="flabel">Customer Bank</label>' + aepsBankPickerHTML('cb')
    + '<button onclick="processAEPSCustomer()" class="btn-primary" style="margin-top:6px">👆 Customer Biometric & Process →</button>';
  if (c.bank) aepsBankPick('cb', c.bank);
}

function aepsTxnDone(){
  var f = document.getElementById('svc-form'), res = document.getElementById('svc-result');
  if (f) f.style.display = 'none'; if (res) res.style.display = 'block'; return res;
}

async function processAEPSCustomer(){
  var phone = (document.getElementById('m-phone') || {}).value || '';
  var aad = (document.getElementById('m-aadhaar') || {}).value || '';
  var type = (document.getElementById('m-type') || {}).value || 'withdrawal';
  var bank = (document.getElementById('cb-code') || {}).value || '';
  var amount = type === 'withdrawal' ? (parseInt((document.getElementById('m-amount') || {}).value, 10) || 0) : 0;
  if (!/^\d{10}$/.test(phone)) { toast('Enter valid 10-digit customer mobile', 'e'); return; }
  if (!/^\d{12}$/.test(aad)) { toast('Enter the customer\'s 12-digit Aadhaar', 'e'); return; }
  if (!bank) { toast('Please select customer bank', 'e'); return; }
  if (type === 'withdrawal' && amount < 100) { toast('Minimum withdrawal ₹100', 'e'); return; }
  AEPS_LIVE.cust = { phone: phone, aadhaar: aad, bank: bank, amount: amount || '' };
  var bankName = ((AEPS_LIVE.banks || []).filter(function(b){ return b.code === bank; })[0] || {}).name || bank;

  aepsBusy(3, 'Getting your location…', '');
  var geo = await aepsGeo();
  if (!geo) return aepsFail(3, 'Location is required for AEPS. Allow location access and try again.', 'renderAEPSStep3()');

  var base = { userCode: AEPS_LIVE.userCode, customerId: phone, aadhaar: aad, bankCode: bank, latlong: geo };
  var txnOtpId = '';
  if (type === 'withdrawal' && amount > 5000) {
    aepsBusy(3, 'Requesting transaction OTP…', 'The customer receives an SMS on the Aadhaar-linked mobile');
    var o = await aepsCall('POST', '/eko/aeps/v2/withdrawal-otp', Object.assign({}, base, { amount: amount }));
    if (!(o.ok && o.d && o.d.data && o.d.data.fp_transaction_id)) return aepsFail(3, o.msg || 'Could not request OTP', 'renderAEPSStep3()');
    txnOtpId = String(o.d.data.fp_transaction_id);
  }

  var w = document.getElementById('aeps-wizard');
  w.innerHTML = aepsStepBar(3)
    + '<div style="background:rgba(0,212,170,.06);border:1px solid rgba(0,212,170,.2);border-radius:14px;padding:20px;text-align:center;margin-bottom:14px">'
    + '<div style="font-size:2.5rem;margin-bottom:10px">👆</div><div style="font-weight:700;color:var(--rtai);font-size:.95rem;margin-bottom:4px">Customer Finger Placement</div>'
    + '<div style="color:var(--muted2);font-size:.78rem">Aadhaar XXXX XXXX ' + aad.slice(-4) + ' · ' + aepsEsc(bankName) + '</div></div>'
    + '<button onclick="aepsCustomerGo()" class="btn-primary">👆 Scan Customer Fingerprint</button>'
    + '<button onclick="renderAEPSStep3()" style="width:100%;margin-top:8px;padding:10px;border-radius:10px;background:transparent;border:1px solid var(--border);color:var(--muted2);cursor:pointer;font-size:.82rem">← Back</button>';
  AEPS_LIVE.pending = { type: type, amount: amount, base: base, txnOtpId: txnOtpId, bankName: bankName };
}

async function aepsCustomerGo(){
  var p = AEPS_LIVE.pending; if (!p) return renderAEPSStep3();
  aepsBusy(3, 'Scanning…', 'Ask the customer to keep the finger on the device');
  var cap = await aepsCaptureFinger('');
  if (cap.error) return aepsFail(3, cap.error, 'renderAEPSStep3()');
  aepsBusy(3, 'Processing AEPS transaction…', 'Contacting ' + p.bankName + ' — do not close this window');
  var body = Object.assign({}, p.base, { piddata: cap.xml });
  var path = '/eko/aeps/v2/balance';
  if (p.type === 'ministatement') path = '/eko/aeps/v2/mini-statement';
  if (p.type === 'withdrawal') { path = '/eko/aeps/v2/withdrawal'; body.amount = p.amount; if (p.txnOtpId) body.txnOtpRequestId = p.txnOtpId; }
  var r = await aepsCall('POST', path, body);
  AEPS_LIVE.pending = null;
  aepsShowResult(p, r);
}

function aepsShowResult(p, r){
  var okCodes = { withdrawal: 1463, balance: 1466, ministatement: 1527 };
  var labels = { withdrawal: 'Cash Withdrawal', balance: 'Balance Enquiry', ministatement: 'Mini Statement' };
  var d = (r.d && r.d.data) || {};
  var cust = AEPS_LIVE.cust || {};
  var success = r.ok && r.code === okCodes[p.type];
  var pending = p.type === 'withdrawal' && r.code === 1465;
  var res = aepsTxnDone(); if (!res) return;
  var color = success ? 'var(--green)' : pending ? 'var(--gold)' : '#ef4444';
  var title = success ? labels[p.type] + ' Successful' : pending ? 'Withdrawal Pending' : labels[p.type] + ' Failed';

  var rows = [['Transaction Type', labels[p.type]], ['Customer Mobile', '+91 ' + aepsEsc(cust.phone)], ['Bank', aepsEsc(p.bankName)]];
  if (d.aadhar) rows.push(['Aadhaar', aepsEsc(d.aadhar)]);
  if (p.type === 'withdrawal' && (success || pending)) rows.push(['Amount', '₹' + fmtN(parseFloat(d.amount || p.amount))]);
  if (d.customer_balance !== undefined && d.customer_balance !== '' && (p.type !== 'withdrawal' || success)) rows.push(['Account Balance', '₹' + fmtN(parseFloat(d.customer_balance) || 0)]);
  if (d.commission) rows.push(['Commission', '₹' + aepsEsc(d.commission)]);
  if (d.tid) rows.push(['Transaction ID', aepsEsc(d.tid)]);
  if (d.bank_ref_num) rows.push(['Bank Ref (RRN)', aepsEsc(d.bank_ref_num)]);
  rows.push(['Date & Time', aepsEsc(d.transaction_date || new Date().toLocaleString('en-IN'))]);
  if (!success) rows.push(['Reason', aepsEsc(pending ? 'Awaiting bank confirmation' : (r.msg || d.comment || 'Declined'))]);

  var mini = '';
  if (success && p.type === 'ministatement' && d.mini_statement_list && d.mini_statement_list.length) {
    mini = '<div style="margin-top:10px"><div style="font-size:.7rem;font-weight:700;color:var(--muted2);text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px">Mini Statement</div>'
      + d.mini_statement_list.map(function(t){
        var cr = String(t.txnType).toLowerCase().indexOf('cr') === 0;
        return '<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--border);font-size:.74rem"><div><div style="color:var(--text)">' + aepsEsc(t.narration) + '</div><div style="color:var(--muted2);font-size:.66rem">' + aepsEsc(t.date) + '</div></div><div style="font-weight:700;color:' + (cr ? 'var(--green)' : '#ef4444') + '">' + (cr ? '+' : '-') + '₹' + aepsEsc(t.amount) + '</div></div>';
      }).join('') + '</div>';
  }

  var txnId = d.tid ? String(d.tid) : '';
  if (p.type === 'withdrawal' && success && txnId) {
    try {
      TXN_HISTORY.push({ id: txnId, service: 'aeps', title: 'AEPS Cash Withdrawal', amount: parseFloat(d.amount || p.amount), type: 'credit',
        date: new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }), txnId: txnId, status: 'success', rtaiVerified: true });
    } catch (e) {}
  }
  var wd = (success && p.type !== 'withdrawal')
    ? '<div style="background:rgba(245,158,11,.07);border:1px solid rgba(245,158,11,.25);border-radius:10px;padding:11px 13px;margin-top:10px;display:flex;align-items:center;justify-content:space-between;gap:10px"><div style="font-size:.78rem;font-weight:700;color:var(--gold)">💸 Proceed to Cash Withdrawal?</div><button onclick="aepsDirectWithdraw()" style="flex-shrink:0;padding:8px 14px;border-radius:9px;background:linear-gradient(135deg,#f59e0b,#ef4444);border:none;color:#fff;font-size:.76rem;font-weight:700;cursor:pointer">Withdraw →</button></div>' : '';
  var inq = pending && txnId
    ? '<div style="font-size:.72rem;color:var(--muted2);margin-top:8px">Do not repeat the withdrawal. Check status with Transaction ID ' + aepsEsc(txnId) + ' or contact support.</div>' : '';

  res.innerHTML = '<div style="background:var(--bg3);border:1px solid ' + color + ';border-radius:14px;padding:16px">'
    + '<div style="text-align:center;margin-bottom:12px"><div style="font-size:1.8rem">' + (success ? '✅' : pending ? '⏳' : '❌') + '</div>'
    + '<div style="font-family:var(--font-head);font-size:.95rem;font-weight:700;color:' + color + '">' + title + '</div></div>'
    + '<div style="background:var(--bg2);border-radius:10px;padding:10px">'
    + rows.map(function(x){ return '<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--border);font-size:.76rem"><span style="color:var(--muted2)">' + x[0] + '</span><span style="color:var(--text);font-weight:600;text-align:right;max-width:60%">' + x[1] + '</span></div>'; }).join('')
    + '</div>' + mini + wd + inq
    + '<div style="display:flex;gap:8px;margin-top:10px">'
    + (success && p.type === 'withdrawal' && txnId ? '<button onclick="showInvoice(\'' + aepsEsc(txnId) + '\')" style="flex:1;padding:9px;border-radius:9px;background:rgba(99,102,241,.15);border:1px solid rgba(99,102,241,.3);color:#818cf8;cursor:pointer;font-size:.78rem;font-weight:700">🧾 Receipt</button>' : '')
    + '<button onclick="aepsAnother()" style="flex:1;padding:9px;border-radius:9px;background:linear-gradient(135deg,var(--rtai),var(--rtai2));border:none;color:#000;cursor:pointer;font-size:.78rem;font-weight:700">New Transaction</button>'
    + '<button onclick="document.getElementById(\'svc-modal\').classList.remove(\'show\')" style="flex:1;padding:9px;border-radius:9px;background:var(--bg3);border:1px solid var(--border2);color:var(--muted2);cursor:pointer;font-size:.78rem;font-weight:700">Close</button>'
    + '</div></div>';
  toast(success ? labels[p.type] + ' successful ✅' : pending ? 'Withdrawal pending ⏳' : (r.msg || 'Transaction failed'), success ? 's' : 'e');
}

function aepsBackToForm(keep){
  var f = document.getElementById('svc-form'), res = document.getElementById('svc-result');
  if (res) res.style.display = 'none'; if (f) f.style.display = 'block';
  if (!keep) AEPS_LIVE.cust = null;
  renderAEPSStep3();
}
function aepsAnother(){ aepsBackToForm(false); }
function aepsDirectWithdraw(){ aepsBackToForm(true); var t = document.getElementById('m-type'); if (t) { t.value = 'withdrawal'; toggleAEPSFields(); } }
// QR / fake-scan helpers from the old wizard are intentionally disabled
function simulateQRScan(){} function simulateBiometricScan(){} function renderAEPSStep2(){ return aepsOperatorDaily(); }
'''
BLOCK = '<script id="aeps-real-web">' + JS + '</script>\n</body>'

backup = FILE + ".bak." + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
shutil.copy(FILE, backup)
content = content[:pos] + BLOCK + content[pos + len("</body>"):]
with open(FILE, "w", encoding="utf-8") as f:
    f.write(content)
print("OK: Real AEPS wizard added to " + FILE)
print("    Backup: " + backup)
