#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Website side of the AEPS wallet credit. Run AFTER add_real_aeps_web.py.
 1) AEPS calls now send the BankMe login token (authFetch) - required by the hardened backend
 2) after a confirmed withdrawal the wallet chip / CU.wallet shows the new balance from the server
 3) the receipt shows "Credited to wallet" (or a warning if Eko paid but the credit failed)

Usage:  cd ~/Desktop/bankme-site && python3 secure_and_wallet_aeps_web.py
"""
import sys, shutil, datetime
FILE = "app.html"
c = open(FILE, "r", encoding="utf-8").read()
R = []

R.append(("authFetch in aepsCall",
"""    var r = await fetch(AEPS_API + path, { method: method, signal: c.signal,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined });
    var j = await r.json();""",
"""    var r = await authFetch(AEPS_API + path, { method: method, signal: c.signal,
      headers: body ? { 'Content-Type': 'application/json' } : {},
      body: body ? JSON.stringify(body) : undefined });
    if (r.status === 401) return { ok: false, d: null, code: null, msg: 'Your session expired. Please log in again.' };
    var j = await r.json();"""))

R.append(("return fields",
"    return { ok: !!j.success, d: d, code: d ? d.response_type_id : null, msg: msg };",
"    return { ok: !!j.success, d: d, code: d ? d.response_type_id : null, msg: msg, nb: j.newBalance, credited: j.credited, creditFailed: !!j.creditFailed };"))

R.append(("wallet update + receipt rows",
"  var txnId = d.tid ? String(d.tid) : '';\n  if (p.type === 'withdrawal' && success && txnId) {",
"""  var txnId = d.tid ? String(d.tid) : '';
  if (p.type === 'withdrawal' && success) {
    if (r.nb !== undefined && r.nb !== null && CU) {
      CU.wallet = r.nb;
      var chipEl = document.getElementById('wallet-chip'); if (chipEl) chipEl.textContent = '\\u20B9' + fmtN(CU.wallet);
    }
    if (r.credited) rows.push(['Credited to your wallet', '\\u20B9' + fmtN(r.credited)]);
    if (r.creditFailed) rows.push(['\\u26A0\\uFE0F Wallet credit', 'FAILED - contact support with Transaction ID ' + aepsEsc(txnId)]);
  }
  if (p.type === 'withdrawal' && success && txnId) {"""))

ok = True
for name, o, n in R:
    k = c.count(o)
    if k != 1:
        ok = False; print("ERROR '%s': expected 1 match, found %d" % (name, k))
if not ok:
    print("Nothing written. Was add_real_aeps_web.py applied (and not edited)? Tell Claude."); sys.exit(1)
for name, o, n in R:
    c = c.replace(o, n, 1)
b = FILE + ".bak." + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
shutil.copy(FILE, b)
open(FILE, "w", encoding="utf-8").write(c)
print("OK: %d changes applied. Backup: %s" % (len(R), b))
