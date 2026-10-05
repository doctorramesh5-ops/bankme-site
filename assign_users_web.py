#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Website Assign screen: also lists accounts from the backend database (so every onboarded
retailer / distributor / super distributor can be assigned), shows their current parent, and
saves assignments for them through the backend link. Run AFTER network_users_web.py and
assign_users_backend.py (backend deployed).

Usage:  cd ~/Desktop/bankme-site && python3 assign_users_web.py
"""
import sys, shutil, datetime
FILE = "app.html"
c = open(FILE, "r", encoding="utf-8").read()
if 'id="assign-users-web"' in c:
    sys.exit("Already applied. Nothing written.")
O1 = "  showAssignTab('retailer');\n}\n\nfunction showAssignTab(type){"
O2 = "if(db&&userUid&&userUid.indexOf('demo-')!==0){\n      await db.collection('bankme_users').doc(userUid).update({assignedTo:parentUid||null});\n    }"
for n, o in (("renderAssign end", O1), ("doAssign firestore update", O2)):
    if c.count(o) != 1:
        sys.exit("ERROR '%s': expected 1 match, found %d. Nothing written. Tell Claude." % (n, c.count(o)))
pos = c.rfind("</body>")
if pos < 0 or c[pos + len("</body>"):].strip() != "</html>":
    sys.exit("ERROR: unexpected end of file. Nothing written.")
N1 = "  await mergeBackendAssignUsers();\n  showAssignTab('retailer');\n}\n\nfunction showAssignTab(type){"
N2 = ("if(db&&userUid&&userUid.indexOf('demo-')!==0&&userUid.indexOf('be-')!==0){\n"
      "      // a parent that only exists in the backend has no website record to point at: the backend link is the source of truth then\n"
      "      await db.collection('bankme_users').doc(userUid).update({assignedTo:(parentUid&&parentUid.indexOf('be-')===0)?null:(parentUid||null)});\n    }")
JS = r'''
async function mergeBackendAssignUsers(){
  if (!CU || CU.role !== 'admin') return;
  try {
    var r = await authFetch(AEPS_API + '/admin/network/users');
    var j = await r.json();
    if (!j || !j.success || !Array.isArray(j.users)) return;
    var all = window._assignUsers || [];
    var norm = function(p){ return String(p || '').replace(/\D/g, '').slice(-10); };
    var byPhone = {};
    all.forEach(function(u){ var p = norm(u.phone || u.mobile); if (p) byPhone[p] = u; });
    j.users.forEach(function(b){
      var p = norm(b.phone); if (!p) return;
      if (!byPhone[p]) {
        var nu = { uid: 'be-' + p, name: b.name || ('User ' + p), email: b.email || p, phone: p, role: b.role || 'customer',
          wallet: b.wallet || 0, kyc: b.kycStatus === 'verified' ? 'verified' : 'pending', shopName: b.shopName || '', assignedTo: null };
        all.push(nu); byPhone[p] = nu;
      } else if (!byPhone[p].role && b.role) { byPhone[p].role = b.role; }
    });
    // parent links held in the backend win over older website values
    j.users.forEach(function(b){
      if (!b.linked) return;
      var child = byPhone[norm(b.phone)]; if (!child) return;
      var par = b.parentPhone ? byPhone[norm(b.parentPhone)] : null;
      child.assignedTo = par ? par.uid : null;
    });
    window._assignUsers = all;
  } catch (e) { /* keep whatever the website already loaded */ }
}
'''
shutil.copy(FILE, FILE + ".bak." + datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
c = c.replace(O1, N1, 1).replace(O2, N2, 1)
pos = c.rfind("</body>")
c = c[:pos] + '<script id="assign-users-web">' + JS + '</script>\n</body>' + c[pos + len("</body>"):]
open(FILE, "w", encoding="utf-8").write(c)
print("OK: Assign screen now includes backend accounts.")
