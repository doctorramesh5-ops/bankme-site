#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Website: stop showing the placeholder name "User 1234" (made from the last 4 digits of the mobile) and use the PAN name.
 1) Profile header + "Name (as per PAN)" row: PAN name when verified; otherwise "Complete your KYC" - never "User 7191"
 2) Eko onboarding form: First / Last name pre-filled from the verified PAN name (also PAN number and date of birth when KYC has them);
    left EMPTY if there is no PAN name (never "User" / "7191"). Placeholder names are refused on submit.

Usage:  cd ~/Desktop/bankme-site && python3 pan_name_web.py
"""
import sys, shutil, datetime
FILE = "app.html"
c = open(FILE, "r", encoding="utf-8").read()
if 'id="pan-name-web"' in c:
    sys.exit("Already applied. Nothing written.")

R = []
R.append(("profile header name",
"font-size:1.1rem;font-weight:700\">'+CU.name+'</div>'",
"font-size:1.1rem;font-weight:700\">'+bmDisplayName()+'</div>'"))
R.append(("profile PAN row",
"['Name (as per PAN)',CU.panName||CU.name]",
"['Name (as per PAN)',CU.panName||(bmNameOk(CU.name)?CU.name:'Not verified \\u2014 complete KYC')]"))
R.append(("onboarding prefill",
"""  var nm = String((CU && CU.name) || '').trim().split(/\\s+/);
  var first = nm.length > 1 ? nm.slice(0, -1).join(' ') : (nm[0] || ''), last = nm.length > 1 ? nm[nm.length - 1] : '';""",
"""  var kyc = await bmLoadKyc();
  var fullName = kyc.panName || (bmNameOk(CU && CU.name) ? CU.name : '');
  var nm = String(fullName).trim().split(/\\s+/).filter(Boolean);
  var first = nm.length > 1 ? nm.slice(0, -1).join(' ') : (nm[0] || ''), last = nm.length > 1 ? nm[nm.length - 1] : '';
  var prePan = /^[A-Z]{5}[0-9]{4}[A-Z]$/.test(String(kyc.panNumber || '').toUpperCase()) ? String(kyc.panNumber).toUpperCase() : '';
  var d8 = String(kyc.dob || '').replace(/\\D/g, ''), preDob = d8.length === 8 ? d8.slice(4) + '-' + d8.slice(2, 4) + '-' + d8.slice(0, 2) : '';"""))
R.append(("onboarding PAN field",
"""+ inp('ob-pan', 'PAN number', 'ABCDE1234F', '', 'maxlength="10\"""",
"""+ inp('ob-pan', 'PAN number', 'ABCDE1234F', prePan, 'maxlength="10\""""))
R.append(("onboarding dob field",
"""'<label class="flabel">Date of birth</label><input class="finp" id="ob-dob" type="date"/>'""",
"""'<label class="flabel">Date of birth</label><input class="finp" id="ob-dob" type="date" value="' + aepsEsc(preDob) + '"/>'"""))
R.append(("onboarding name check",
"if (!body.firstName || !body.lastName) { toast('Enter your first and last name', 'e'); return; }",
"if (!body.firstName || !body.lastName) { toast('Enter your first and last name as on your PAN card', 'e'); return; }\n  if (!bmNameOk(body.firstName + ' ' + body.lastName)) { toast('Enter your real name as on the PAN card', 'e'); return; }"))

for n, o, nw in R:
    if c.count(o) != 1:
        sys.exit("ERROR '%s': expected 1 match, found %d. Nothing written. Tell Claude." % (n, c.count(o)))
pos = c.rfind("</body>")
if pos < 0 or c[pos + len("</body>"):].strip() != "</html>":
    sys.exit("ERROR: unexpected end of file. Nothing written.")

JS = r'''
// "User 7191" style names are placeholders created at first login, never real names
function bmNameOk(n){ n = String(n == null ? '' : n).trim(); return !!n && !/^user\s*\d{0,4}$/i.test(n); }
function bmDisplayName(){
  if (!CU) return '';
  if (CU.panName) return aepsEsc(CU.panName);
  if (bmNameOk(CU.name)) return aepsEsc(CU.name);
  return '<span style="color:var(--gold);font-size:.9rem">Complete your KYC to add your name</span>';
}
async function bmLoadKyc(){
  var phone = String((CU && (CU.phone || CU.mobile)) || '').replace(/\D/g, '').slice(-10);
  if (CU && CU.panName && CU.panNumber) return { panName: CU.panName, panNumber: CU.panNumber, dob: CU.dob };
  if (phone.length !== 10) return {};
  try {
    var r = await fetch(BACKEND_URL + '/user/' + phone + '/kyc-status'); var d = await r.json();
    if (d && d.success) return { panName: bmNameOk(d.panName) ? d.panName : '', panNumber: d.panNumber || '', dob: d.dob || '' };
  } catch (e) {}
  return {};
}
'''
shutil.copy(FILE, FILE + ".bak." + datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
for n, o, nw in R:
    c = c.replace(o, nw, 1)
pos = c.rfind("</body>")
c = c[:pos] + '<script id="pan-name-web">' + JS + '</script>\n</body>' + c[pos + len("</body>"):]
open(FILE, "w", encoding="utf-8").write(c)
print("OK: placeholder names hidden; Eko form uses the PAN name.")
