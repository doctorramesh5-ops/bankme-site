#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Website: after a customer finishes Eko onboarding the account becomes a Retailer (website record + screen),
and the onboarding form tells customers this will happen. Run AFTER onboard_agent_web.py and customer_upgrade_backend.py (deployed).
Usage:  cd ~/Desktop/bankme-site && python3 customer_upgrade_web.py
"""
import sys, shutil, datetime
FILE = "app.html"
c = open(FILE, "r", encoding="utf-8").read()
if 'id="customer-upgrade-web"' in c:
    sys.exit("Already applied. Nothing written.")
O1 = "AEPS_LIVE.userCode = String(r.d.userCode);\n"
O2 = "then you continue to the one-time activation.</div></div>'"
for n, o in (("onboard success", O1), ("form notice", O2)):
    if c.count(o) != 1:
        sys.exit("ERROR '%s': expected 1 match, found %d. Is onboard_agent_web.py applied? Nothing written." % (n, c.count(o)))
pos = c.rfind("</body>")
if pos < 0 or c[pos + len("</body>"):].strip() != "</html>":
    sys.exit("ERROR: unexpected end of file. Nothing written.")
N1 = "AEPS_LIVE.userCode = String(r.d.userCode);\n  if (r.d.promoted) await bmApplyRetailerUpgrade(r.d);\n"
N2 = "then you continue to the one-time activation.</div>' + (CU && CU.role === 'customer' ? '<div style=\"font-size:.74rem;color:var(--gold);margin-top:8px;line-height:1.5\">⚠️ AEPS is for retailers. Completing this form upgrades your account from Customer to <strong>Retailer</strong>.</div>' : '') + '</div>'"
JS = r'''
async function bmApplyRetailerUpgrade(d){
  try {
    if (CU) { CU.role = 'retailer'; if (d.internalId) CU.internalId = d.internalId; }
    if (db && CU && CU.uid && String(CU.uid).indexOf('demo-') !== 0) {
      await db.collection('bankme_users').doc(CU.uid).update({ role: 'retailer', ekoUserCode: String(d.userCode || '') }).catch(function(){});
    }
    var rc = getRC('retailer'), badge = document.getElementById('role-badge');
    if (badge) { badge.textContent = rc.label; badge.style.background = rc.color + '20'; badge.style.color = rc.color; badge.style.border = '1px solid ' + rc.color + '40'; }
    var nm = document.getElementById('nb-mynetwork'); if (nm) nm.style.display = '';
    toast('Your account is now a Retailer account ✅', 's');
  } catch (e) {}
}
'''
shutil.copy(FILE, FILE + ".bak." + datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
c = c.replace(O1, N1, 1).replace(O2, N2, 1)
pos = c.rfind("</body>")
c = c[:pos] + '<script id="customer-upgrade-web">' + JS + '</script>\n</body>' + c[pos + len("</body>"):]
open(FILE, "w", encoding="utf-8").write(c)
print("OK: customer -> retailer upgrade wired into the AEPS onboarding.")
