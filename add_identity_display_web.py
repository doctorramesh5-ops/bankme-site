#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Displays each account's BankMe internal ID (e.g. BM-RT000042) and Eko user
code in the website header, next to the wallet balance chip. Fetches from
the new backend endpoint GET /user/:phone/identity (added by
add_identity_endpoint_backend.py — run that in bankme-backend FIRST, or
this will just silently find nothing to show).

Works for every role (CR/RT/DS/SDS/WL) since it's keyed off the backend's
existing per-role internalId scheme — confirmed via
ROLE_PREFIX={customer:'CR',retailer:'RT',distributor:'DS',superdist:'SDS',
whitelabel:'WL'} in server.js.

Hooks into showApp() — the single function every login path (all 6 of
them) calls right after setting CU — so this works regardless of which
login path was used, without touching each one individually.

Safe by design: both blocks below must match the CURRENT file text EXACTLY
ONCE before anything is written.

Usage:
    cd ~/Desktop/bankme-site
    python3 add_identity_display_web.py
"""
import sys, shutil, datetime

FILE = "app.html"

with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

replacements = []

# 1) Add the chip element next to wallet-chip in the header
old1 = '      <span class="wallet-chip" id="wallet-chip">₹0.00</span>'
new1 = ('      <span class="wallet-chip" id="wallet-chip">₹0.00</span>\n'
        '      <span class="wallet-chip" id="identity-chip" style="display:none"></span>')
replacements.append(("header identity-chip element", old1, new1))

# 2) Add fetchMyIdentity() function + call it from showApp()
old2 = """  document.getElementById('wallet-chip').textContent='\\u20B9'+fmtN(CU.wallet||0);"""
new2 = """  document.getElementById('wallet-chip').textContent='\\u20B9'+fmtN(CU.wallet||0);
  fetchMyIdentity();"""
replacements.append(("showApp() calls fetchMyIdentity()", old2, new2))

old3 = "function showApp(){"
new3 = """async function fetchMyIdentity(){
  try{
    if(!CU||!CU.phone) return;
    var r=await fetch(BANKME_API+'/user/'+CU.phone+'/identity');
    var j=await r.json();
    if(j&&j.success){
      CU.internalId=j.internalId||null;
      CU.ekoUserCode=j.ekoUserCode||null;
      var chip=document.getElementById('identity-chip');
      if(chip&&(CU.internalId||CU.ekoUserCode)){
        chip.style.display='inline-block';
        chip.textContent=(CU.internalId||'')+(CU.ekoUserCode?' \\u00b7 Eko '+CU.ekoUserCode:'');
        chip.title='Your BankMe Internal ID'+(CU.ekoUserCode?' and Eko User Code':'');
      }
    }
  }catch(e){ /* identity display is non-critical \\u2014 fail silently */ }
}

function showApp(){"""
replacements.append(("add fetchMyIdentity() before showApp()", old3, new3))

ok = True
for name, old, new in replacements:
    count = content.count(old)
    if count != 1:
        ok = False
        print(f"❌ '{name}': expected to find the old text exactly once, found {count}.")
        print("   -> Your file has changed since this script was written against it.")
        print("   -> Nothing has been written. Tell Claude and paste the relevant section fresh.")

if not ok:
    sys.exit(1)

for name, old, new in replacements:
    content = content.replace(old, new, 1)

backup = FILE + ".bak." + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
shutil.copy(FILE, backup)
with open(FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"✅ All {len(replacements)} changes applied successfully in {FILE}")
print(f"   Backup of the previous version saved as {backup}")
