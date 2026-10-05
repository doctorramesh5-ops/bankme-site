#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Follow-up fix for BBPS on the website (app.html), after fix_bbps_web.py.

Fixes two real bugs found during testing:
  1. Eko rejects sender_name if it contains anything but letters/spaces
     (error seen: "Sender Name should contain only letters"). Your
     shop/profile name can contain digits (e.g. "User 7191"), which broke
     both fetch-bill and would have broken pay-bill too.
  2. The "Consumer" row in the fetched-bill card was falling back to your
     OWN retailer name whenever Eko didn't return a customer name for that
     biller (common for several electricity boards) — showing your name
     instead of the biller's customer, or nothing at all. Now it simply
     omits that row when Eko doesn't supply a real customer name, instead
     of substituting your identity.

Safe by design: every block below must match the CURRENT file text
EXACTLY ONCE (or the stated expected count) before anything is written.
If it doesn't match, the whole run aborts and your file is untouched.

Usage:
    cd ~/Desktop/bankme-site
    python3 fix_bbps_sender_name.py
"""
import sys, shutil, datetime

FILE = "app.html"

with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

replacements = []  # list of (name, old, new, expected_count)

# ─────────────────────────────────────────────────────────────────
# 1) Add a sender-name sanitizer helper (letters/spaces only)
# ─────────────────────────────────────────────────────────────────
old1 = """function bbpsStyleFor(name){
  for(var i=0;i<BBPS_CAT_STYLE.length;i++){ if(BBPS_CAT_STYLE[i].match.test(name||'')) return BBPS_CAT_STYLE[i]; }
  return BBPS_DEFAULT_STYLE;
}"""

new1 = """function bbpsStyleFor(name){
  for(var i=0;i<BBPS_CAT_STYLE.length;i++){ if(BBPS_CAT_STYLE[i].match.test(name||'')) return BBPS_CAT_STYLE[i]; }
  return BBPS_DEFAULT_STYLE;
}
// Eko's BBPS sender_name param rejects anything but letters/spaces
// (real error seen: "Sender Name should contain only letters").
function bbpsSenderName(){
  var raw=(CU&&(CU.shopName||CU.name))||'';
  var letters=String(raw).replace(/[^A-Za-z ]/g,'').replace(/\\s+/g,' ').trim();
  return letters||'Retailer';
}"""

replacements.append(("add bbpsSenderName() helper", old1, new1, 1))

# ─────────────────────────────────────────────────────────────────
# 2) fetchBBPSBill — use sanitized sender name
# ─────────────────────────────────────────────────────────────────
old2 = """  var catObj=BBPS_CATEGORIES.find(function(c){return c.id===cat;})||{label:cat,icon:'🧾'};
  var senderName=(CU&&(CU.shopName||CU.name))||'Retailer';"""

new2 = """  var catObj=BBPS_CATEGORIES.find(function(c){return c.id===cat;})||{label:cat,icon:'🧾'};
  var senderName=bbpsSenderName();"""

replacements.append(("fetchBBPSBill sender name (sanitized)", old2, new2, 1))

# ─────────────────────────────────────────────────────────────────
# 3) fetchBBPSBill — don't show retailer's own name as "Consumer"
# ─────────────────────────────────────────────────────────────────
old3 = """    var billAmt=Number(d.amount||d.bill_amount||0);
    var consumerName=d.customerName||d.customer_name||senderName;
    var dueDateStr=d.dueDate||d.due_date||'';
    var billNumber=d.billNumber||d.bill_number||d.bill_id||('BILL'+consumer.slice(-6));

    window._bbpsFetchedAmt=billAmt;

    var rows=[
      ['👤 Consumer',consumerName],
      ['🏢 Biller',biller.name],
      ['🧾 Bill No.',billNumber],
    ].concat(dueDateStr?[['📆 Due Date',dueDateStr]]:[]).concat([
      ['💰 Bill Amount','<span style="font-family:var(--font-head);font-size:1rem;font-weight:700;color:var(--green)">₹'+fmtN(billAmt)+'</span>'],
    ]);"""

new3 = """    var billAmt=Number(d.amount||d.bill_amount||0);
    var consumerName=d.customerName||d.customer_name||d.consumer_name||d.customerFullName||'';
    var dueDateStr=d.dueDate||d.due_date||'';
    var billNumber=d.billNumber||d.bill_number||d.bill_id||('BILL'+consumer.slice(-6));

    window._bbpsFetchedAmt=billAmt;

    var rows=[].concat(consumerName?[['👤 Consumer',consumerName]]:[]).concat([
      ['🏢 Biller',biller.name],
      ['🧾 Bill No.',billNumber],
    ]).concat(dueDateStr?[['📆 Due Date',dueDateStr]]:[]).concat([
      ['💰 Bill Amount','<span style="font-family:var(--font-head);font-size:1rem;font-weight:700;color:var(--green)">₹'+fmtN(billAmt)+'</span>'],
    ]);"""

replacements.append(("fetchBBPSBill Consumer row (omit instead of fake)", old3, new3, 1))

# ─────────────────────────────────────────────────────────────────
# 4) processService 'bbps' branch — use sanitized sender name
# ─────────────────────────────────────────────────────────────────
old4 = """    if(totalDebit>(CU.wallet||0)){ toast('Insufficient wallet balance (need ₹'+fmtN(totalDebit)+')','e'); return; }
    var senderName=(CU&&(CU.shopName||CU.name))||'Retailer';"""

new4 = """    if(totalDebit>(CU.wallet||0)){ toast('Insufficient wallet balance (need ₹'+fmtN(totalDebit)+')','e'); return; }
    var senderName=bbpsSenderName();"""

replacements.append(("processService bbps sender name (sanitized)", old4, new4, 1))

# ─────────────────────────────────────────────────────────────────
# Dry-run check: every OLD must appear the expected number of times
# ─────────────────────────────────────────────────────────────────
ok = True
for name, old, new, expected in replacements:
    count = content.count(old)
    if count != expected:
        ok = False
        print(f"❌ '{name}': expected {expected} match(es), found {count}.")
        print("   -> Your file has changed since this script was written against it.")
        print("   -> Nothing has been written. Tell Claude and paste the relevant section fresh.")

if not ok:
    sys.exit(1)

for name, old, new, expected in replacements:
    content = content.replace(old, new, expected)

backup = FILE + ".bak." + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
shutil.copy(FILE, backup)
with open(FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"✅ All {len(replacements)} fixes applied successfully in {FILE}")
print(f"   Backup of the previous version saved as {backup}")
