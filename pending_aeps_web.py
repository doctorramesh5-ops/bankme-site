#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Website side of pending AEPS withdrawals. Run AFTER fix_aeps_txn_otp_web.py
(and after the backend script pending_aeps_backend.py is deployed).
A pending withdrawal now shows a "Check status" button: the server asks Eko; on success the
wallet is credited once and the chip updates; on failure it says so.

Usage:  cd ~/Desktop/bankme-site && python3 pending_aeps_web.py
"""
import sys, shutil, datetime
FILE = "app.html"
c = open(FILE, "r", encoding="utf-8").read()
R = []

R.append(("pending button",
"""  var inq = pending && txnId
    ? '<div style="font-size:.72rem;color:var(--muted2);margin-top:8px">Do not repeat the withdrawal. Check status with Transaction ID ' + aepsEsc(txnId) + ' or contact support.</div>' : '';""",
"""  var inq = pending && txnId
    ? '<div style="font-size:.72rem;color:var(--muted2);margin-top:8px">Do not repeat the withdrawal. Transaction ID ' + aepsEsc(txnId) + '</div>'
      + '<button id="aeps-recon-btn" onclick="aepsReconcile(\\'' + aepsEsc(txnId) + '\\')" style="width:100%;margin-top:8px;padding:10px;border-radius:9px;background:rgba(245,158,11,.12);border:1px solid rgba(245,158,11,.4);color:var(--gold);cursor:pointer;font-size:.8rem;font-weight:700">🔄 Check status with Eko</button>'
      + '<div id="aeps-recon-msg" style="font-size:.76rem;margin-top:8px;text-align:center"></div>' : '';"""))

R.append(("reconcile function",
"function aepsBackToForm(keep){",
"""async function aepsReconcile(tid){
  var btn = document.getElementById('aeps-recon-btn'), msg = document.getElementById('aeps-recon-msg');
  if (btn) { btn.disabled = true; btn.textContent = 'Checking…'; }
  // this route answers { success, state, ... } directly (not Eko-shaped), so call it with authFetch once
  var res = null, httpStatus = 0;
  try {
    var x = await authFetch(AEPS_API + '/eko/aeps/v2/reconcile', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ tid: tid }) });
    httpStatus = x.status; res = await x.json();
  } catch (e) { res = null; }
  if (btn) { btn.disabled = false; btn.textContent = '🔄 Check status with Eko'; }
  if (!res || !res.success) {
    if (msg) { msg.style.color = '#ef4444'; msg.textContent = httpStatus === 401 ? 'Your session expired. Please log in again.' : ((res && res.error) || 'Could not check right now. Try again shortly.'); }
    return;
  }
  if (res.state === 'success') {
    if (res.newBalance !== undefined && res.newBalance !== null && CU) {
      CU.wallet = res.newBalance;
      var chip = document.getElementById('wallet-chip'); if (chip) chip.textContent = '\\u20B9' + fmtN(CU.wallet);
    }
    if (msg) { msg.style.color = 'var(--green)'; msg.textContent = res.credited ? '✅ Confirmed — ₹' + fmtN(res.credited) + ' credited to your wallet' : '✅ Confirmed — already credited'; }
    if (btn) btn.style.display = 'none';
    toast('Withdrawal confirmed ✅', 's');
  } else if (res.state === 'failed') {
    if (msg) { msg.style.color = '#ef4444'; msg.textContent = '❌ The withdrawal failed at the bank. Nothing was credited.'; }
    if (btn) btn.style.display = 'none';
  } else {
    if (msg) { msg.style.color = 'var(--gold)'; msg.textContent = '⏳ Still waiting for the bank. Check again in a few minutes.'; }
  }
}

function aepsBackToForm(keep){"""))

ok = True
for name, o, n in R:
    k = c.count(o)
    if k != 1:
        ok = False; print("ERROR '%s': expected 1 match, found %d" % (name, k))
if not ok:
    print("Nothing written. Tell Claude."); sys.exit(1)
for name, o, n in R:
    c = c.replace(o, n, 1)
b = FILE + ".bak." + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
shutil.copy(FILE, b)
open(FILE, "w", encoding="utf-8").write(c)
print("OK: %d changes applied. Backup: %s" % (len(R), b))
