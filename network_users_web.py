#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Website: My Network (admin) now also lists accounts that exist in the backend database,
merged with the website's own user records by mobile number (no duplicates).
Needs the backend script network_users_backend.py deployed first.

Usage:  cd ~/Desktop/bankme-site && python3 network_users_web.py
"""
import sys, shutil, datetime
FILE = "app.html"
c = open(FILE, "r", encoding="utf-8").read()
if 'id="network-users-web"' in c:
    sys.exit("Already applied. Nothing written.")
OLD = """commissionEarned:2000*i});});
  }
  if(myTabs.length){
    showNetworkTab(myTabs[0]);"""
if c.count(OLD) != 1:
    sys.exit("ERROR 'renderMyNetwork anchor': expected 1 match, found %d. Nothing written. Tell Claude." % c.count(OLD))
NEW = """commissionEarned:2000*i});});
  }
  await mergeBackendNetworkUsers();
  if(myTabs.length){
    showNetworkTab(myTabs[0]);"""
pos = c.rfind("</body>")
if pos < 0 or c[pos + len("</body>"):].strip() != "</html>":
    sys.exit("ERROR: unexpected end of file. Nothing written.")
JS = r'''
async function mergeBackendNetworkUsers(){
  if (!CU || CU.role !== 'admin') return;
  try {
    var r = await authFetch(AEPS_API + '/admin/network/users');
    var j = await r.json();
    if (!j || !j.success || !Array.isArray(j.users)) return;
    var all = window._networkUsers || [];
    var byPhone = {};
    all.forEach(function(u){ var p = String(u.phone || u.mobile || '').replace(/\D/g, '').slice(-10); if (p) byPhone[p] = u; });
    j.users.forEach(function(b){
      var p = String(b.phone || '').replace(/\D/g, '').slice(-10);
      if (!p) return;
      var ex = byPhone[p];
      if (ex) {
        if (!ex.role && b.role) ex.role = b.role;
        if (!ex.phone) ex.phone = p;
        if (ex.kyc !== 'verified' && b.kycStatus === 'verified') ex.kyc = 'verified';
        return;
      }
      var d = b.createdAt ? new Date(b.createdAt) : null;
      all.push({
        uid: 'be-' + p, name: b.name || ('User ' + p), email: b.email || p, phone: p, role: b.role || 'customer',
        wallet: b.wallet || 0, kyc: b.kycStatus === 'verified' ? 'verified' : 'pending', shopName: b.shopName || '',
        joined: d ? d.toLocaleDateString('en-IN', { month: 'short', year: 'numeric' }) : 'New',
        txns: [], rtaiScore: 80, commissionEarned: 0, internalId: b.internalId || '', ekoUserCode: b.ekoUserCode || ''
      });
    });
    window._networkUsers = all;
  } catch (e) { /* backend list is a bonus: keep whatever the website already loaded */ }
}
'''
shutil.copy(FILE, FILE + ".bak." + datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
c = c.replace(OLD, NEW, 1)
pos = c.rfind("</body>")
c = c[:pos] + '<script id="network-users-web">' + JS + '</script>\n</body>' + c[pos + len("</body>"):]
open(FILE, "w", encoding="utf-8").write(c)
print("OK: My Network now merges backend accounts.")
