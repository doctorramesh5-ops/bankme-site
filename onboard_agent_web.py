#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Website: when a retailer has no Eko code, AEPS now shows an "Eko retailer onboarding" form
(PAN, name, email, date of birth, shop, address). Submitting it calls POST /eko/aeps/v2/onboard
(backend script onboard_agent_backend.py must be deployed first), then continues to the
one-time AEPS activation.

Usage:  cd ~/Desktop/bankme-site && python3 onboard_agent_web.py
"""
import sys, shutil, datetime
FILE = "app.html"
c = open(FILE, "r", encoding="utf-8").read()
if 'id="aeps-onboard-web"' in c:
    sys.exit("Already applied. Nothing written.")

OLD1 = "return aepsFail(1, 'Your account is not linked to an Eko retailer code yet, so AEPS cannot run. Contact BankMe support.', 'initAEPSWizard()');"
OLD2 = "return aepsFail(1, 'Your account has no Eko retailer code yet. Complete retailer onboarding first.', 'initAEPSWizard()');"
for name, o in (("wizard no-code message", OLD1), ("activation no-code message", OLD2)):
    if c.count(o) != 1:
        sys.exit("ERROR '%s': expected 1 match, found %d. Nothing written. Tell Claude." % (name, c.count(o)))
if c.count("</body>") < 1 or not c.rstrip().endswith("</html>"):
    sys.exit("ERROR: unexpected end of file. Nothing written.")
pos = c.rfind("</body>")
if c[pos + len("</body>"):].strip() != "</html>":
    sys.exit("ERROR: last </body> is not followed only by </html>. Nothing written.")

JS = r'''
async function aepsOnboardForm(){
  var w = document.getElementById('aeps-wizard'); if (!w) return;
  var procBtn = document.querySelector('#svc-form .btn-primary'); if (procBtn) procBtn.style.display = 'none';
  try { if (typeof aepsActLoadLists === 'function') await aepsActLoadLists(); } catch (e) {}
  var states = (typeof AEPS_ACT !== 'undefined' && AEPS_ACT.states) || [];
  var nm = String((CU && CU.name) || '').trim().split(/\s+/);
  var first = nm.length > 1 ? nm.slice(0, -1).join(' ') : (nm[0] || ''), last = nm.length > 1 ? nm[nm.length - 1] : '';
  function inp(id, label, ph, val, extra){ return '<label class="flabel">' + label + '</label><input class="finp" id="' + id + '" placeholder="' + (ph || '') + '" value="' + aepsEsc(val || '') + '" ' + (extra || '') + '/>'; }
  var stateField = states.length
    ? '<label class="flabel">State</label><select class="fsel" id="ob-state"><option value="">-- Select State --</option>' + states.map(function(s){ return '<option value="' + aepsEsc(s.name) + '">' + aepsEsc(s.name) + '</option>'; }).join('') + '</select>'
    : inp('ob-state', 'State', 'e.g. Tamil Nadu');
  w.innerHTML = '<div style="background:rgba(245,158,11,.07);border:1px solid rgba(245,158,11,.28);border-radius:12px;padding:12px;margin-bottom:14px">'
    + '<div style="font-weight:700;color:var(--gold);font-size:.88rem;margin-bottom:4px">Eko retailer onboarding (one time)</div>'
    + '<div style="font-size:.74rem;color:var(--muted2);line-height:1.55">Your account has no Eko retailer code yet. Enter your details exactly as on your PAN card. This creates <strong>your own</strong> AEPS agent code, then you continue to the one-time activation.</div></div>'
    + inp('ob-first', 'First name (as on PAN)', 'First name', first)
    + inp('ob-last', 'Last name (as on PAN)', 'Last name', last)
    + inp('ob-pan', 'PAN number', 'ABCDE1234F', '', 'maxlength="10" style="text-transform:uppercase;letter-spacing:2px" oninput="this.value=this.value.toUpperCase().replace(/[^A-Z0-9]/g,\'\')"')
    + inp('ob-email', 'Email', 'name@example.com', (CU && CU.email) || '', 'type="email"')
    + '<label class="flabel">Date of birth</label><input class="finp" id="ob-dob" type="date"/>'
    + inp('ob-shop', 'Shop name', 'Shop name', (CU && CU.shopName) || '')
    + inp('ob-line', 'Address line', 'Shop / door no, street')
    + inp('ob-area', 'Area / locality', 'Area')
    + inp('ob-city', 'City', 'City')
    + inp('ob-district', 'District', 'District')
    + stateField
    + inp('ob-pin', 'Pincode', '6-digit pincode', '', 'type="tel" maxlength="6" oninput="this.value=this.value.replace(/[^0-9]/g,\'\')"')
    + '<div style="font-size:.7rem;color:var(--muted2);margin:-4px 0 12px">Mobile used: ' + aepsEsc((CU && (CU.phone || CU.mobile)) || '') + ' (your login number). 🔒 PAN is sent securely to Eko and not stored by BankMe.</div>'
    + '<button onclick="aepsOnboardSubmit()" class="btn-primary">Create my Eko retailer code →</button>';
}

async function aepsOnboardSubmit(){
  function v(id){ return ((document.getElementById(id) || {}).value || '').trim(); }
  var body = {
    firstName: v('ob-first'), lastName: v('ob-last'), panNumber: v('ob-pan').toUpperCase(), email: v('ob-email'),
    dob: v('ob-dob'), shopName: v('ob-shop'),
    address: { line: v('ob-line'), area: v('ob-area'), city: v('ob-city'), district: v('ob-district'), state: v('ob-state'), pincode: v('ob-pin') }
  };
  if (!body.firstName || !body.lastName) { toast('Enter your first and last name', 'e'); return; }
  if (!/^[A-Z]{5}[0-9]{4}[A-Z]$/.test(body.panNumber)) { toast('Enter a valid PAN (ABCDE1234F)', 'e'); return; }
  if (!/^\S+@\S+\.\S+$/.test(body.email)) { toast('Enter a valid email', 'e'); return; }
  if (!body.dob) { toast('Select your date of birth', 'e'); return; }
  if (!body.shopName) { toast('Enter your shop name', 'e'); return; }
  if (!body.address.line || !body.address.city || !body.address.district || !body.address.state || !/^\d{6}$/.test(body.address.pincode)) { toast('Complete the address (line, city, district, state, 6-digit pincode)', 'e'); return; }
  aepsBusy(1, 'Creating your Eko retailer code…', 'Verifying your PAN with Eko. This can take up to a minute');
  var r = await aepsCall('POST', '/eko/aeps/v2/onboard', body);
  if (!(r.ok && r.d && r.d.userCode)) return aepsFail(1, r.msg || 'Eko could not onboard this retailer. Check the details match your PAN card.', 'aepsOnboardForm()');
  AEPS_LIVE.userCode = String(r.d.userCode);
  try { if (CU) CU.ekoUserCode = AEPS_LIVE.userCode; } catch (e) {}
  var w = document.getElementById('aeps-wizard');
  w.innerHTML = '<div style="background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.35);border-radius:14px;padding:20px;text-align:center;margin-bottom:16px">'
    + '<div style="font-size:2.4rem;margin-bottom:8px">✅</div>'
    + '<div style="font-family:var(--font-head);font-size:1.05rem;font-weight:700;color:var(--green);margin-bottom:4px">Eko retailer code created</div>'
    + '<div style="font-size:.8rem;color:var(--muted2)">Your code: <strong style="color:var(--text)">' + aepsEsc(AEPS_LIVE.userCode) + '</strong></div>'
    + '<div style="font-size:.74rem;color:var(--muted2);margin-top:8px;line-height:1.5">Next: the one-time AEPS activation (shop details, documents and photos).</div></div>'
    + '<button onclick="aepsActivationOpen()" class="btn-primary">Continue to AEPS activation →</button>';
}
'''
BLOCK = '<script id="aeps-onboard-web">' + JS + '</script>\n</body>'
backup = FILE + ".bak." + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
shutil.copy(FILE, backup)
c = c.replace(OLD1, "return aepsOnboardForm();", 1).replace(OLD2, "return aepsOnboardForm();", 1)
pos = c.rfind("</body>")
c = c[:pos] + BLOCK + c[pos + len("</body>"):]
open(FILE, "w", encoding="utf-8").write(c)
print("OK: Eko onboarding form added. Backup: " + backup)
