#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proper fix for the "No key for Response" case on the website's BBPS flow,
replacing the two earlier quick patches (fix_bbps_zero_amount.py and
fix_bbps_allow_zero_due.py) with correct handling.

Real-world finding (confirmed by testing): Eko returns a message-only
response with no amount field in two legitimate situations, not just one:
  1. The biller has nothing due this cycle (confirmed directly against
     TNEB's own website for the same account).
  2. The biller is a prepaid/recharge-type service (e.g. Jio Prepaid) that
     doesn't support auto bill-fetch under BBPS at all — you're expected
     to just key in a recharge amount.
Neither of these is an error. This patch shows a clear, honest "no amount
available automatically — enter manually" card in both cases, instead of
either a scary error message or a fake ₹0.00 "bill".

Safe by design: the block below must match the CURRENT file text EXACTLY
ONCE before anything is written. If it doesn't match, nothing is written.

Usage:
    cd ~/Desktop/bankme-site
    python3 fix_bbps_no_data_case.py
"""
import sys, shutil, datetime

FILE = "app.html"

with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

old = """    var r=await fetch(BANKME_API+'/eko/bbps/fetch-bill?'+qs);
    var j=await r.json();
    if(j&&j.success===false){ throw new Error(j.message||'Could not fetch bill'); }
    var d=(j&&j.data)||j||{};
    if(d&&d.message&&d.amount==null&&d.bill_amount==null){ throw new Error(d.message||'Could not fetch bill. Please wait a few seconds and try again.'); }
    var billAmt=Number(d.amount||d.bill_amount||0);
    // Note: ₹0 is a legitimate "nothing due this cycle" result for many
    // billers (confirmed against TNEB directly) — do NOT treat it as an error.
    var consumerName=d.customerName||d.customer_name||d.consumer_name||d.customerFullName||'';
    var dueDateStr=d.dueDate||d.due_date||'';
    var billNumber=d.billNumber||d.bill_number||d.bill_id||('BILL'+consumer.slice(-6));

    window._bbpsFetchedAmt=billAmt;

    var rows=[].concat(consumerName?[['👤 Consumer',consumerName]]:[]).concat([
      ['🏢 Biller',biller.name],
      ['🧾 Bill No.',billNumber],
    ]).concat(dueDateStr?[['📆 Due Date',dueDateStr]]:[]).concat([
      ['💰 Bill Amount','<span style="font-family:var(--font-head);font-size:1rem;font-weight:700;color:var(--green)">₹'+fmtN(billAmt)+'</span>'],
    ]);

    bc.innerHTML='<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">'
      +'<div style="font-size:1.2rem">'+catObj.icon+'</div>'
      +'<div style="font-size:.82rem;font-weight:700;color:var(--green)">Bill Fetched Successfully</div>'
      +'<div style="margin-left:auto;font-size:.65rem;background:rgba(16,185,129,.15);color:var(--green);padding:2px 7px;border-radius:100px;font-weight:700">NPCI BBPS</div>'
      +'</div>'
      +'<div style="background:var(--bg2);border-radius:8px;padding:8px 10px">'
      +rows.map(function(r){
        return '<div style="display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid var(--border);font-size:.76rem">'
          +'<span style="color:var(--muted2)">'+r[0]+'</span>'
          +'<span style="color:var(--text);text-align:right;max-width:55%">'+r[1]+'</span></div>';
      }).join('')
      +'</div>';

    var amtEl=document.getElementById('bbps-amount');
    if(amtEl) amtEl.value=billAmt||'';
    var totalEl=document.getElementById('bbps-total-amt');
    if(totalEl) totalEl.textContent=billAmt?'₹'+fmtN(billAmt+10):'₹—';
    if(as) as.style.display='block';
    if(!silent) toast('Bill fetched! ₹'+fmtN(billAmt)+' due','s');"""

new = """    var r=await fetch(BANKME_API+'/eko/bbps/fetch-bill?'+qs);
    var j=await r.json();
    if(j&&j.success===false){ throw new Error(j.message||'Could not fetch bill'); }
    var d=(j&&j.data)||j||{};
    var hasAmount=(d.amount!=null||d.bill_amount!=null);
    var billAmt=Number(d.amount||d.bill_amount||0);
    var consumerName=d.customerName||d.customer_name||d.consumer_name||d.customerFullName||'';
    var dueDateStr=d.dueDate||d.due_date||'';
    var billNumber=d.billNumber||d.bill_number||d.bill_id||('BILL'+consumer.slice(-6));

    window._bbpsFetchedAmt=hasAmount?billAmt:null;

    if(!hasAmount){
      // No auto-fetchable amount — either nothing is due this cycle, or this
      // biller is a prepaid/recharge type that doesn't support bill-fetch at
      // all (e.g. Jio Prepaid). Let the retailer key in the amount manually
      // instead of guessing or showing a fake ₹0.00.
      bc.innerHTML='<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">'
        +'<div style="font-size:1.2rem">'+catObj.icon+'</div>'
        +'<div style="font-size:.82rem;font-weight:700;color:var(--text)">'+biller.name+'</div>'
        +'</div>'
        +'<div style="font-size:.76rem;color:var(--muted2)">No bill amount available automatically for this account right now (either nothing is due, or this biller does not support auto bill-fetch). Enter the amount manually below.</div>';
      var amtEl0=document.getElementById('bbps-amount');
      if(amtEl0) amtEl0.value='';
      var totalEl0=document.getElementById('bbps-total-amt');
      if(totalEl0) totalEl0.textContent='₹—';
      if(as) as.style.display='block';
      if(!silent) toast('No bill amount available — enter it manually','s');
      return;
    }

    var rows=[].concat(consumerName?[['👤 Consumer',consumerName]]:[]).concat([
      ['🏢 Biller',biller.name],
      ['🧾 Bill No.',billNumber],
    ]).concat(dueDateStr?[['📆 Due Date',dueDateStr]]:[]).concat([
      ['💰 Bill Amount','<span style="font-family:var(--font-head);font-size:1rem;font-weight:700;color:var(--green)">₹'+fmtN(billAmt)+'</span>'],
    ]);

    bc.innerHTML='<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">'
      +'<div style="font-size:1.2rem">'+catObj.icon+'</div>'
      +'<div style="font-size:.82rem;font-weight:700;color:var(--green)">Bill Fetched Successfully</div>'
      +'<div style="margin-left:auto;font-size:.65rem;background:rgba(16,185,129,.15);color:var(--green);padding:2px 7px;border-radius:100px;font-weight:700">NPCI BBPS</div>'
      +'</div>'
      +'<div style="background:var(--bg2);border-radius:8px;padding:8px 10px">'
      +rows.map(function(r){
        return '<div style="display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid var(--border);font-size:.76rem">'
          +'<span style="color:var(--muted2)">'+r[0]+'</span>'
          +'<span style="color:var(--text);text-align:right;max-width:55%">'+r[1]+'</span></div>';
      }).join('')
      +'</div>';

    var amtEl=document.getElementById('bbps-amount');
    if(amtEl) amtEl.value=billAmt||'';
    var totalEl=document.getElementById('bbps-total-amt');
    if(totalEl) totalEl.textContent=billAmt?'₹'+fmtN(billAmt+10):'₹—';
    if(as) as.style.display='block';
    if(!silent) toast('Bill fetched! ₹'+fmtN(billAmt)+' due','s');"""

count = content.count(old)
if count != 1:
    print(f"❌ Expected to find the target text exactly once, found {count}.")
    print("   -> Your file has changed since this script was written against it.")
    print("   -> Nothing has been written. Tell Claude and paste the relevant section fresh.")
    sys.exit(1)

content = content.replace(old, new, 1)

backup = FILE + ".bak." + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
shutil.copy(FILE, backup)
with open(FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"✅ Fix applied successfully in {FILE}")
print(f"   Backup of the previous version saved as {backup}")
