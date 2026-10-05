#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Go-live clean-up of the website's fake data:
 1) Fraud Engine : invented alerts / random "transactions per second" removed -> honest page
 2) Reconcile    : random totals and fake bank settlements removed -> REAL ledger summary + items needing attention
 3) Disputes     : TXN001-TXN005 sample rows removed; admin sees the REAL ledger
 4) Disputes     : "Reverse" no longer credits any wallet in the browser (it records a reversal REQUEST only);
                   "check status" no longer fakes a result.
Needs golive_clean_backend.py deployed first.

Usage:  cd ~/Desktop/bankme-site && python3 golive_clean_web.py
"""
import sys, re, shutil, datetime
FILE = "app.html"
c = open(FILE, "r", encoding="utf-8").read()
if 'id="golive-clean-web"' in c:
    sys.exit("Already applied. Nothing written.")
pat = re.compile(r"  // Add mock dispute data for demo\n  if\(!allTxns\.length\)\{\n    allTxns = \[\n.*?\n    \];\n  \}\n", re.S)
if len(pat.findall(c)) != 1:
    sys.exit("ERROR 'mock dispute block': expected 1 match, found %d. Nothing written. Tell Claude." % len(pat.findall(c)))
for need in ("function renderFraudEngine(){", "function renderReconcile(){", "function renderDispute(){", "function initiateReversal(txnId){", "function checkTxnStatus(txnId){"):
    if c.count(need) != 1:
        sys.exit("ERROR: '%s' not found exactly once. Nothing written." % need)
pos = c.rfind("</body>")
if pos < 0 or c[pos + len("</body>"):].strip() != "</html>":
    sys.exit("ERROR: unexpected end of file. Nothing written.")

JS = r'''
// ---------- shared: real ledger (admin) ----------
var _GL = { rows: null, at: 0 };
async function glLoadLedger(force){
  if (!force && _GL.rows && Date.now() - _GL.at < 15000) return _GL.rows;
  try {
    var r = await authFetch(AEPS_API + '/admin/ledger?limit=500');
    var j = await r.json();
    if (j && j.success && Array.isArray(j.transactions)) { _GL.rows = j.transactions; _GL.at = Date.now(); return _GL.rows; }
  } catch (e) {}
  return null;
}
function glMoney(n){ return '₹' + (Number(n) || 0).toLocaleString('en-IN'); }
function glCard(label, val, col){ return '<div style="background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:12px;text-align:center"><div style="font-family:var(--font-head);font-size:1.15rem;font-weight:700;color:' + col + '">' + val + '</div><div style="font-size:.68rem;color:var(--muted2);margin-top:3px">' + label + '</div></div>'; }

// ---------- Fraud Engine: honest page, no invented alerts ----------
renderFraudEngine = function(){
  var el = document.getElementById('page-fraud'); if (!el) return;
  var controls = [
    ['🔐', 'Login required', 'Every AEPS, network and admin API call needs a valid login token'],
    ['🚫', 'One wallet credit per Eko transaction', 'A withdrawal can never credit the wallet twice'],
    ['❄️', 'Frozen accounts blocked', 'Frozen retailers cannot run AEPS'],
    ['👆', 'Biometric + OTP', 'Aadhaar fingerprint on every AEPS call; customer SMS OTP above ₹5,000'],
    ['⏳', 'Pending withdrawals', 'Held as pending until Eko confirms; no cash credit before confirmation']
  ];
  el.innerHTML = '<div class="page-title" style="color:var(--red)">🔍 Fraud Engine</div>'
    + '<div class="page-sub">Controls enforced by the platform · real alerts only</div>'
    + '<div style="font-family:var(--font-head);font-size:.95rem;font-weight:700;margin-bottom:10px">🚨 Fraud Alerts</div>'
    + '<div style="background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:26px;text-align:center;color:var(--muted2);margin-bottom:18px"><div style="font-size:2rem;margin-bottom:6px">✅</div><div style="font-size:.88rem">No fraud alerts recorded.</div><div style="font-size:.72rem;margin-top:4px">Alerts will appear here when the platform flags a real transaction.</div></div>'
    + '<div style="font-family:var(--font-head);font-size:.95rem;font-weight:700;margin-bottom:10px">🛡️ Controls in force</div>'
    + '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px">'
    + controls.map(function(x){ return '<div style="background:var(--bg2);border:1px solid rgba(0,212,170,.2);border-radius:12px;padding:12px"><div style="font-size:1.3rem;margin-bottom:5px">' + x[0] + '</div><div style="font-size:.82rem;font-weight:600;color:var(--text);margin-bottom:3px">' + x[1] + '</div><div style="font-size:.7rem;color:var(--muted2)">' + x[2] + '</div></div>'; }).join('')
    + '</div>';
};

// ---------- Reconcile: REAL ledger ----------
renderReconcile = async function(){
  var el = document.getElementById('page-reconcile'); if (!el) return;
  el.innerHTML = '<div class="page-title">📒 Reconcile</div><div class="page-sub">Real transaction ledger</div><div style="text-align:center;padding:30px;color:var(--muted2)">⏳ Loading ledger…</div>';
  var rows = await glLoadLedger(true);
  if (!rows) { el.innerHTML = '<div class="page-title">📒 Reconcile</div><div style="padding:24px;color:#ef4444">Could not load the ledger. Log in as admin and try again.</div>'; return; }
  var by = {}, tot = { n: 0, ok: 0, pend: 0, fail: 0, att: 0 };
  rows.forEach(function(t){
    var k = t.mainService || 'other'; by[k] = by[k] || { n: 0, cr: 0, dr: 0, pend: 0, fail: 0 };
    by[k].n++; tot.n++;
    if (t.status === 'success') { tot.ok++; if (t.type === 'credit') by[k].cr += t.amount; else by[k].dr += t.amount; }
    else if (t.status === 'pending') { by[k].pend++; tot.pend++; }
    else { by[k].fail++; tot.fail++; }
  });
  var attention = rows.filter(function(t){ return t.status !== 'success'; });
  function when(d){ try { return new Date(d).toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }); } catch (e) { return ''; } }
  var svcRows = Object.keys(by).map(function(k){ var b = by[k];
    return '<tr style="border-bottom:1px solid var(--border)"><td style="padding:8px 10px;font-size:.8rem;font-weight:600">' + k.toUpperCase() + '</td><td style="padding:8px 10px;font-size:.78rem">' + b.n + '</td><td style="padding:8px 10px;font-size:.78rem;color:var(--green)">' + glMoney(b.cr) + '</td><td style="padding:8px 10px;font-size:.78rem;color:#ef4444">' + glMoney(b.dr) + '</td><td style="padding:8px 10px;font-size:.78rem;color:var(--gold)">' + b.pend + '</td><td style="padding:8px 10px;font-size:.78rem;color:#ef4444">' + b.fail + '</td></tr>'; }).join('');
  var attRows = attention.slice(0, 100).map(function(t){
    return '<tr style="border-bottom:1px solid var(--border)"><td style="padding:7px 10px;font-size:.74rem">' + aepsEsc(when(t.createdAt)) + '</td><td style="padding:7px 10px;font-size:.74rem">' + aepsEsc((t.mainService || '') + (t.subService ? ' / ' + t.subService : '')) + '</td><td style="padding:7px 10px;font-size:.74rem">' + aepsEsc(t.userName || t.phone) + '</td><td style="padding:7px 10px;font-size:.74rem">' + glMoney(t.amount) + '</td><td style="padding:7px 10px;font-size:.74rem;color:' + (t.status === 'pending' ? 'var(--gold)' : '#ef4444') + '">' + aepsEsc(t.status) + '</td><td style="padding:7px 10px;font-size:.7rem;color:var(--muted2)">' + aepsEsc(t.reference) + '</td></tr>'; }).join('');
  var th = function(s){ return '<th style="padding:8px 10px;text-align:left;font-size:.68rem;color:var(--muted2)">' + s + '</th>'; };
  el.innerHTML = '<div class="page-title">📒 Reconcile</div><div class="page-sub">Real transaction ledger · latest ' + rows.length + ' entries</div>'
    + '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;margin-bottom:18px">'
    + glCard('Entries', tot.n, 'var(--cyan)') + glCard('Successful', tot.ok, 'var(--green)') + glCard('Pending', tot.pend, 'var(--gold)') + glCard('Failed / other', tot.fail, '#ef4444') + '</div>'
    + (rows.length ? '' : '<div style="text-align:center;padding:26px;color:var(--muted2)">No transactions yet.</div>')
    + (rows.length ? '<div style="font-family:var(--font-head);font-size:.92rem;font-weight:700;margin-bottom:8px">By service</div><div style="background:var(--bg2);border:1px solid var(--border);border-radius:12px;overflow:auto;margin-bottom:18px"><table style="width:100%;border-collapse:collapse;min-width:480px"><thead><tr style="background:var(--bg3)">' + th('SERVICE') + th('ENTRIES') + th('CREDITED') + th('DEBITED') + th('PENDING') + th('FAILED') + '</tr></thead><tbody>' + svcRows + '</tbody></table></div>' : '')
    + '<div style="font-family:var(--font-head);font-size:.92rem;font-weight:700;margin-bottom:8px">Needs attention (' + attention.length + ')</div>'
    + (attention.length ? '<div style="background:var(--bg2);border:1px solid var(--border);border-radius:12px;overflow:auto"><table style="width:100%;border-collapse:collapse;min-width:520px"><thead><tr style="background:var(--bg3)">' + th('TIME') + th('SERVICE') + th('USER') + th('AMOUNT') + th('STATUS') + th('REFERENCE') + '</tr></thead><tbody>' + attRows + '</tbody></table></div>'
      : '<div style="background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:22px;text-align:center;color:var(--muted2);font-size:.85rem">✅ Nothing pending or failed.</div>');
};

// ---------- Disputes: admin sees the REAL ledger; no money moves in the browser ----------
var _origRenderDispute = renderDispute;
renderDispute = async function(){
  try {
    if (CU && (CU.role === 'admin' || CU.role === 'whitelabel')) {
      var rows = await glLoadLedger(false);
      if (rows) window._allNetworkTxns = rows.map(function(t){
        var d = t.createdAt ? new Date(t.createdAt) : null;
        return { txnId: t.reference || (t.phone + '-' + (d ? d.getTime() : '')), title: (t.mainService || 'txn') + (t.subService ? ' / ' + t.subService : ''), service: t.mainService, amount: t.amount, type: t.type,
          status: t.status, date: d ? d.toLocaleDateString('en-IN') : '', userName: t.userName || t.phone, userRole: t.userRole, phone: t.phone, disputeStatus: 'none' };
      });
    }
  } catch (e) {}
  _origRenderDispute();
};

// A reversal never credits a wallet from the browser (wallets live on the server). It records a request only.
initiateReversal = function(txnId){
  if (!confirm('Record a reversal request for ' + txnId + '?\nNo money moves until it is verified with the payment partner and credited from the server.')) return;
  TXN_HISTORY.forEach(function(x){ if (x.txnId === txnId) { x.disputeStatus = 'reversal'; } });
  if (db && CU && CU.uid) {
    db.collection('bankme_disputes').add({ txnId: txnId, type: 'reversal', raisedBy: CU.uid, raisedByName: CU.name, raisedByRole: CU.role, date: nowStr(), status: 'open' }).catch(function(){});
    db.collection('bankme_users').doc(CU.uid).update({ txns: TXN_HISTORY }).catch(function(){});
  }
  toast('Reversal request recorded for ' + txnId + ' — no wallet change', 's');
  renderDispute();
};

// No simulated outcome: AEPS withdrawals are checked with Eko; other services have no live check yet.
checkTxnStatus = async function(txnId){
  var t = (TXN_HISTORY || []).filter(function(x){ return x.txnId === txnId; })[0];
  if (!t || t.service !== 'aeps') { toast('Live status check is only available for AEPS withdrawals right now', 'i'); return; }
  toast('Checking with Eko…', 'i');
  try {
    var r = await authFetch(AEPS_API + '/eko/aeps/v2/reconcile', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ tid: txnId }) });
    var j = await r.json();
    if (!j || !j.success) { toast((j && j.error) || 'Could not check status', 'e'); return; }
    if (j.state === 'success') { t.status = 'success'; toast('Confirmed by Eko' + (j.credited ? ' — wallet credited' : ''), 's'); }
    else if (j.state === 'failed') { t.status = 'failed'; toast('Failed at the bank — nothing credited', 'e'); }
    else toast('Still pending at the bank', 'i');
    renderDispute();
  } catch (e) { toast('Could not check status', 'e'); }
};
'''
shutil.copy(FILE, FILE + ".bak." + datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
c = pat.sub("", c, count=1)
pos = c.rfind("</body>")
c = c[:pos] + '<script id="golive-clean-web">' + JS + '</script>\n</body>' + c[pos + len("</body>"):]
open(FILE, "w", encoding="utf-8").write(c)
print("OK: fake Fraud / Reconcile / Dispute data removed; real ledger wired in.")
