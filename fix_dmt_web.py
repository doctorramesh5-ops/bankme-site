#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rewires DMT on the BankMe website (app.html) from the entirely simulated
version (fake "verify account" with a random name, fake OTP, local wallet
math, fake Bulk/Schedule tabs with zero backend support) to the REAL Eko
flow, matching exactly what mobile's DMTScreen.tsx already does against
bankme-backend:

  1. Verify/onboard the SENDER (the customer sending money) by mobile number
  2. Add or pick a RECIPIENT (beneficiary bank account)
  3. Send OTP to the sender
  4. Confirm transfer with that OTP

Confirmed from mobile's real, working implementation:
  - Real per-transaction limit is ₹100–₹5,000 (not the old fake ₹10,000/
    ₹25,000 daily/monthly limits)
  - DMT does NOT touch the BankMe in-app wallet at all (runs on Eko's own
    float) — confirmed by grepping mobile's DMTScreen.tsx for any wallet
    reference: zero matches
  - channel/state are currently hardcoded ('1'/'24') on mobile too (marked
    TODO there for multi-state support) — mirrored here for parity

This replaces the ENTIRE old DMT block (DMT_STATE, DMT_LIMITS, and every
function from loadDMTBeneficiaries through saveSchedule) with the new real
implementation. The old Bulk Transfer and Schedule Transfer tabs are
removed — they had no backend support at all and risked a retailer
believing a "scheduled" transfer would actually happen.

Safe by design: locates the block by start/end markers and aborts with no
changes if either marker isn't found exactly once (meaning the file has
changed since this script was written against it).

Usage:
    cd ~/Desktop/bankme-site
    python3 fix_dmt_web.py
"""
import sys, shutil, datetime

FILE = "app.html"

with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

start_marker = "var DMT_STATE = {"
end_marker = "  toast('Transfer scheduled! RTAI will notify before execution ✅','s');\n}"

start_count = content.count(start_marker)
end_count = content.count(end_marker)
if start_count != 1 or end_count != 1:
    print(f"❌ Could not uniquely locate the DMT block (start matches={start_count}, end matches={end_count}).")
    print("   -> Your file has changed since this script was written against it.")
    print("   -> Nothing has been written. Tell Claude and paste the relevant section fresh.")
    sys.exit(1)

start_idx = content.find(start_marker)
end_idx = content.find(end_marker) + len(end_marker)
old_block = content[start_idx:end_idx]

new_block = """var DMT_BANKS = ['State Bank of India','Punjab National Bank','Bank of Baroda','Canara Bank','Union Bank','Bank of India','HDFC Bank','ICICI Bank','Axis Bank','Kotak Mahindra','Yes Bank','IndusInd Bank','IDBI Bank','Federal Bank','Karnataka Bank','South Indian Bank','UCO Bank','Central Bank','Bank of Maharashtra','Indian Bank','Post Office (IPPB)','Airtel Payments Bank','Paytm Payments Bank','Fino Payments Bank'];

// Real DMT state (sender -> recipient -> OTP -> transfer), matching mobile exactly
var DMT = {
  senderMobile: '',
  senderName: '',
  senderStatus: 'none', // none | needs_onboarding | kyc_pending | ready
  savedRecipients: [],
  recipientId: null,
  amount: 0,
  remarks: '',
  otpRefId: '',
  txnResult: null,
  _beneInfo: null,
};

function dmtAgentPhone(){ return (CU&&CU.phone)||''; }
function dmtRoot(){ return document.getElementById('dmt-root'); }

function renderDMT(){
  DMT.senderMobile=''; DMT.senderName=''; DMT.senderStatus='none';
  DMT.savedRecipients=[]; DMT.recipientId=null; DMT.amount=0; DMT.remarks='';
  DMT.otpRefId=''; DMT.txnResult=null; DMT._beneInfo=null;
  dmtRenderStep1();
}

function dmtRenderStep1(){
  var root=dmtRoot(); if(!root) return;
  root.innerHTML =
    '<div style="background:rgba(0,212,170,.05);border:1px solid rgba(0,212,170,.2);border-radius:12px;padding:12px;margin-bottom:14px;font-size:.76rem;color:var(--rtai)">🛡️ Domestic Money Transfer via NPCI/Eko · ₹100–₹5,000 per transaction</div>'
    +'<label class="flabel">Sender Mobile Number</label>'
    +'<input class="finp" id="dmt-sender-mobile" type="tel" maxlength="10" placeholder="10-digit mobile of person sending money"/>'
    +'<div id="dmt-sender-result" style="display:none;margin-bottom:10px"></div>'
    +'<button class="btn-primary" id="dmt-verify-btn" onclick="dmtVerifySender()" style="background:linear-gradient(135deg,var(--blue),var(--cyan))">🔍 Verify Sender →</button>'
    +'<div id="dmt-onboard-section" style="display:none;margin-top:14px"></div>';
}

async function dmtVerifySender(){
  var mobile=(document.getElementById('dmt-sender-mobile')?.value||'').trim();
  if(!mobile||mobile.length!==10){ toast('Enter a valid 10-digit sender mobile number','e'); return; }
  var agentPhone=dmtAgentPhone();
  if(!agentPhone){ toast('Could not identify your account. Please log in again.','e'); return; }
  DMT.senderMobile=mobile;
  var btn=document.getElementById('dmt-verify-btn');
  var res=document.getElementById('dmt-sender-result');
  if(btn){ btn.disabled=true; btn.textContent='Verifying…'; }
  if(res){ res.style.display='block'; res.innerHTML='<div style="font-size:.78rem;color:var(--muted2)">🔍 Verifying sender with Eko…</div>'; }
  try{
    var r=await fetch(BANKME_API+'/eko/dmt/sender/'+mobile+'?agent_phone='+encodeURIComponent(agentPhone));
    var j=await r.json();
    var rt=j&&j.data&&j.data.response_type_id;
    if(rt===309){
      DMT.senderName=(j.data.data&&j.data.data.customer_profile&&j.data.data.customer_profile.name)||'Verified Sender';
      DMT.senderStatus='ready';
      if(res) res.innerHTML='<div style="background:rgba(16,185,129,.1);border:1px solid var(--green);border-radius:8px;padding:9px;font-size:.78rem"><span style="color:var(--green);font-weight:600">✅ Sender Verified</span><div style="color:var(--muted2);margin-top:2px">'+DMT.senderName+'</div></div>';
      await dmtFetchRecipients();
      setTimeout(dmtRenderStep2,400);
    } else if(rt===2134){
      DMT.senderName=mobile;
      DMT.senderStatus='kyc_pending';
      if(res) res.innerHTML='<div style="background:rgba(245,158,11,.1);border:1px solid var(--gold);border-radius:8px;padding:9px;font-size:.78rem"><span style="color:var(--gold);font-weight:600">⚠️ KYC Pending</span><div style="color:var(--muted2);margin-top:2px">Sender can still transfer with limits.</div></div>';
      await dmtFetchRecipients();
      setTimeout(dmtRenderStep2,400);
    } else if(rt===308){
      DMT.senderStatus='needs_onboarding';
      if(res) res.style.display='none';
      dmtShowOnboardForm();
    } else {
      toast((j&&j.data&&j.data.message)||'Could not verify sender','e');
    }
  }catch(e){
    toast('Network error — could not reach server','e');
  }finally{
    if(btn){ btn.disabled=false; btn.textContent='🔍 Verify Sender →'; }
  }
}

function dmtShowOnboardForm(){
  var sec=document.getElementById('dmt-onboard-section');
  if(!sec) return;
  sec.style.display='block';
  sec.innerHTML =
    '<div style="font-size:.8rem;font-weight:700;color:var(--text);margin-bottom:8px">New sender — complete registration</div>'
    +'<label class="flabel">Sender Full Name</label>'
    +'<input class="finp" id="dmt-ob-name" placeholder="Full name as per ID"/>'
    +'<label class="flabel">Date of Birth</label>'
    +'<input class="finp" id="dmt-ob-dob" type="date"/>'
    +'<label class="flabel">Address Line</label>'
    +'<input class="finp" id="dmt-ob-line" placeholder="House / Street"/>'
    +'<label class="flabel">City</label>'
    +'<input class="finp" id="dmt-ob-city" placeholder="City"/>'
    +'<label class="flabel">District</label>'
    +'<input class="finp" id="dmt-ob-district" placeholder="District (optional, defaults to city)"/>'
    +'<label class="flabel">State</label>'
    +'<input class="finp" id="dmt-ob-state" placeholder="State"/>'
    +'<label class="flabel">Pincode</label>'
    +'<input class="finp" id="dmt-ob-pincode" maxlength="6" placeholder="6-digit pincode"/>'
    +'<label class="flabel">Area</label>'
    +'<input class="finp" id="dmt-ob-area" placeholder="Area (optional, defaults to address line)"/>'
    +'<button class="btn-primary" id="dmt-onboard-btn" onclick="dmtOnboardSender()" style="background:linear-gradient(135deg,var(--blue),var(--cyan))">Register Sender →</button>';
}

async function dmtOnboardSender(){
  var name=(document.getElementById('dmt-ob-name')?.value||'').trim();
  var dob=(document.getElementById('dmt-ob-dob')?.value||'').trim();
  var line=(document.getElementById('dmt-ob-line')?.value||'').trim();
  var city=(document.getElementById('dmt-ob-city')?.value||'').trim();
  var district=(document.getElementById('dmt-ob-district')?.value||'').trim();
  var state=(document.getElementById('dmt-ob-state')?.value||'').trim();
  var pincode=(document.getElementById('dmt-ob-pincode')?.value||'').trim();
  var area=(document.getElementById('dmt-ob-area')?.value||'').trim();
  if(!line||!city||!state||!pincode){ toast('Please fill in sender address details','e'); return; }
  if(!dob){ toast('Please enter sender date of birth','e'); return; }
  var btn=document.getElementById('dmt-onboard-btn');
  if(btn){ btn.disabled=true; btn.textContent='Registering…'; }
  try{
    var r=await fetch(BANKME_API+'/eko/dmt/onboard-sender/'+DMT.senderMobile,{
      method:'POST', headers:{'content-type':'application/json'},
      body:JSON.stringify({
        name: name||('Sender '+DMT.senderMobile), dob:dob, line:line, city:city,
        state:state, pincode:pincode, district:district||city, area:area||line
      })
    });
    var j=await r.json();
    if(j&&j.data&&j.data.status===0){
      DMT.senderName=name||DMT.senderMobile;
      DMT.senderStatus='kyc_pending';
      toast('Sender registered!','s');
      await dmtFetchRecipients();
      setTimeout(dmtRenderStep2,400);
    } else {
      toast((j&&j.data&&j.data.message)||'Could not register sender','e');
    }
  }catch(e){
    toast('Network error — could not reach server','e');
  }finally{
    if(btn){ btn.disabled=false; btn.textContent='Register Sender →'; }
  }
}

async function dmtFetchRecipients(){
  try{
    var r=await fetch(BANKME_API+'/eko/dmt/recipients/'+DMT.senderMobile);
    var j=await r.json();
    DMT.savedRecipients=(j&&j.data&&j.data.data&&j.data.data.recipient_list)||[];
  }catch(e){ DMT.savedRecipients=[]; }
}

function dmtRenderStep2(){
  var root=dmtRoot(); if(!root) return;
  var hasSaved=DMT.savedRecipients&&DMT.savedRecipients.length>0;
  root.innerHTML =
    '<div style="font-size:.78rem;color:var(--muted2);margin-bottom:10px">Sender: <strong style="color:var(--text)">'+(DMT.senderName||DMT.senderMobile)+'</strong> ('+DMT.senderMobile+')'+(DMT.senderStatus==='kyc_pending'?' <span style="color:var(--gold)">· KYC Pending</span>':'')+'</div>'
    +(hasSaved?('<div style="font-size:.74rem;font-weight:700;color:var(--muted2);text-transform:uppercase;margin-bottom:8px">Saved Recipients</div>'
      +'<div id="dmt-saved-list" style="margin-bottom:14px">'
      +DMT.savedRecipients.map(function(r,i){
        var acc=String(r.account||'');
        var masked=acc.length>=8?acc.substring(0,4)+'****'+acc.slice(-4):acc;
        return '<div style="display:flex;align-items:center;justify-content:space-between;background:var(--bg2);border:1px solid var(--border);border-radius:10px;padding:10px 12px;margin-bottom:7px;cursor:pointer" onclick="dmtSelectRecipient('+i+')">'
          +'<div><div style="font-size:.84rem;font-weight:600;color:var(--text)">'+(r.name||r.recipient_name||'Recipient')+'</div>'
          +'<div style="font-size:.7rem;color:var(--muted2)">'+masked+' · '+(r.bank||'')+' · '+(r.ifsc||'')+'</div></div>'
          +'<div style="color:var(--blue);font-size:.76rem;font-weight:700">Select →</div></div>';
      }).join('')
      +'</div>'
      +'<button onclick="dmtShowAddRecipientForm()" style="background:none;border:1px dashed var(--border2);color:var(--muted2);border-radius:10px;padding:9px;width:100%;cursor:pointer;font-size:.78rem;margin-bottom:10px">+ Add a new recipient</button>'
    ):'')
    +'<div id="dmt-add-recipient-form"'+(hasSaved?' style="display:none"':'')+'></div>';
  if(!hasSaved) dmtRenderAddRecipientForm();
}

function dmtShowAddRecipientForm(){
  var f=document.getElementById('dmt-add-recipient-form');
  if(!f) return;
  f.style.display='block';
  dmtRenderAddRecipientForm();
}

function dmtRenderAddRecipientForm(){
  var f=document.getElementById('dmt-add-recipient-form');
  if(!f) return;
  f.innerHTML =
    '<label class="flabel">Recipient Name</label>'
    +'<input class="finp" id="dmt-bene-name" placeholder="Beneficiary full name"/>'
    +'<label class="flabel">Recipient Mobile Number</label>'
    +'<input class="finp" id="dmt-bene-mobile" type="tel" maxlength="10" placeholder="10-digit mobile"/>'
    +'<label class="flabel">Account Number</label>'
    +'<input class="finp" id="dmt-bene-account" placeholder="Bank account number"/>'
    +'<label class="flabel">Confirm Account Number</label>'
    +'<input class="finp" id="dmt-bene-confirm" placeholder="Re-enter account number"/>'
    +'<label class="flabel">IFSC Code</label>'
    +'<input class="finp" id="dmt-bene-ifsc" maxlength="11" placeholder="e.g. SBIN0001234" oninput="this.value=this.value.toUpperCase()"/>'
    +'<label class="flabel">Bank Name</label>'
    +'<select class="fsel" id="dmt-bene-bank">'
    +'<option value="">Select Bank</option>'
    +DMT_BANKS.map(function(b){return '<option value="'+b+'">'+b+'</option>';}).join('')
    +'</select>'
    +'<button class="btn-primary" id="dmt-add-recipient-btn" onclick="dmtAddRecipient()" style="background:linear-gradient(135deg,var(--blue),var(--cyan))">Add Recipient →</button>';
}

function dmtSelectRecipient(idx){
  var r=DMT.savedRecipients[idx];
  if(!r) return;
  DMT.recipientId=r.recipient_id;
  dmtRenderStep3({name:r.name||r.recipient_name||'Recipient',account:r.account,bank:r.bank,ifsc:r.ifsc});
}

async function dmtAddRecipient(){
  var name=(document.getElementById('dmt-bene-name')?.value||'').trim();
  var mobile=(document.getElementById('dmt-bene-mobile')?.value||'').trim();
  var account=(document.getElementById('dmt-bene-account')?.value||'').trim();
  var confirmAcc=(document.getElementById('dmt-bene-confirm')?.value||'').trim();
  var ifsc=(document.getElementById('dmt-bene-ifsc')?.value||'').trim();
  var bank=(document.getElementById('dmt-bene-bank')?.value||'').trim();
  if(!name){ toast('Enter beneficiary name','e'); return; }
  if(!mobile||mobile.length!==10){ toast('Enter beneficiary 10-digit mobile number','e'); return; }
  if(!account||account.length<9){ toast('Enter valid account number','e'); return; }
  if(account!==confirmAcc){ toast('Account numbers do not match','e'); return; }
  if(!ifsc||ifsc.length!==11){ toast('Enter valid 11-character IFSC code','e'); return; }
  var btn=document.getElementById('dmt-add-recipient-btn');
  if(btn){ btn.disabled=true; btn.textContent='Adding…'; }
  try{
    var r=await fetch(BANKME_API+'/eko/dmt/add-recipient/'+DMT.senderMobile,{
      method:'POST', headers:{'content-type':'application/json'},
      body:JSON.stringify({recipient_mobile:mobile, recipient_name:name, ifsc:ifsc, account:account, bank:bank, agent_phone:dmtAgentPhone()})
    });
    var j=await r.json();
    if(j&&j.data&&j.data.data&&j.data.data.recipient_id){
      DMT.recipientId=j.data.data.recipient_id;
      dmtRenderStep3({name:name,account:account,bank:bank,ifsc:ifsc});
    } else if(((j&&j.data&&j.data.message)||'').toLowerCase().indexOf('already registered')!==-1){
      await dmtFetchRecipients();
      var match=DMT.savedRecipients.find(function(x){return x.account===account;});
      if(match){
        DMT.recipientId=match.recipient_id;
        dmtRenderStep3({name:match.name||name,account:account,bank:bank,ifsc:ifsc});
      } else {
        toast('Recipient already registered but could not be located. Try again.','e');
      }
    } else {
      toast((j&&j.data&&j.data.message)||'Could not add recipient','e');
    }
  }catch(e){
    toast('Network error — could not reach server','e');
  }finally{
    if(btn){ btn.disabled=false; btn.textContent='Add Recipient →'; }
  }
}

function dmtRenderStep3(beneInfo){
  var root=dmtRoot(); if(!root) return;
  DMT._beneInfo=beneInfo;
  root.innerHTML =
    '<div style="background:var(--bg2);border:1px solid var(--border);border-radius:10px;padding:10px;margin-bottom:12px;font-size:.78rem">'
    +'<div style="color:var(--muted2)">Sending to</div>'
    +'<div style="font-weight:700;color:var(--text)">'+beneInfo.name+'</div>'
    +'<div style="color:var(--muted2);font-size:.72rem">'+(beneInfo.account||'')+' · '+(beneInfo.bank||'')+' · '+(beneInfo.ifsc||'')+'</div>'
    +'</div>'
    +'<label class="flabel">Amount (₹100 – ₹5,000)</label>'
    +'<input class="finp" id="dmt-amount" type="number" min="100" max="5000" placeholder="Enter amount"/>'
    +'<label class="flabel">Remarks</label>'
    +'<input class="finp" id="dmt-remarks" placeholder="e.g. Family support"/>'
    +'<button class="btn-primary" id="dmt-send-otp-btn" onclick="dmtSendOtp()" style="background:linear-gradient(135deg,var(--blue),var(--cyan))">Send OTP →</button>'
    +'<div id="dmt-otp-section" style="display:none;margin-top:14px"></div>';
}

async function dmtSendOtp(){
  var amount=parseFloat(document.getElementById('dmt-amount')?.value)||0;
  var remarks=(document.getElementById('dmt-remarks')?.value||'').trim()||'Transfer';
  if(!amount||amount<=0){ toast('Enter transfer amount','e'); return; }
  if(amount<100){ toast('Minimum DMT transfer is ₹100','e'); return; }
  if(amount>5000){ toast('DMT limit is ₹5,000 per transaction','e'); return; }
  if(!DMT.recipientId){ toast('Recipient not set — go back and re-add beneficiary','e'); return; }
  DMT.amount=amount; DMT.remarks=remarks;
  var btn=document.getElementById('dmt-send-otp-btn');
  if(btn){ btn.disabled=true; btn.textContent='Sending OTP…'; }
  try{
    var r=await fetch(BANKME_API+'/eko/dmt/send-otp',{
      method:'POST', headers:{'content-type':'application/json'},
      body:JSON.stringify({recipient_id:DMT.recipientId, amount:amount, customer_id:DMT.senderMobile})
    });
    var j=await r.json();
    if(j&&j.data&&j.data.data&&j.data.data.otp_ref_id){
      DMT.otpRefId=j.data.data.otp_ref_id;
      toast('OTP sent to '+DMT.senderMobile,'s');
      var sec=document.getElementById('dmt-otp-section');
      if(sec){
        sec.style.display='block';
        sec.innerHTML =
          '<label class="flabel">Enter OTP sent to '+DMT.senderMobile+'</label>'
          +'<input class="finp" id="dmt-otp" maxlength="6" placeholder="6-digit OTP"/>'
          +'<button class="btn-primary" id="dmt-confirm-btn" onclick="dmtConfirmTransfer()" style="background:linear-gradient(135deg,var(--green),var(--rtai))">Confirm Transfer →</button>';
      }
    } else {
      toast((j&&j.data&&j.data.message)||'Could not send OTP','e');
    }
  }catch(e){
    toast('Network error — could not reach server','e');
  }finally{
    if(btn){ btn.disabled=false; btn.textContent='Send OTP →'; }
  }
}

async function dmtConfirmTransfer(){
  var otp=(document.getElementById('dmt-otp')?.value||'').trim();
  if(!otp||otp.length<4){ toast('Enter the OTP','e'); return; }
  var btn=document.getElementById('dmt-confirm-btn');
  if(btn){ btn.disabled=true; btn.textContent='Processing…'; }
  try{
    var r=await fetch(BANKME_API+'/eko/dmt/initiate-transfer',{
      method:'POST', headers:{'content-type':'application/json'},
      body:JSON.stringify({recipient_id:DMT.recipientId, amount:DMT.amount, customer_id:DMT.senderMobile, otp:otp, otp_ref_id:DMT.otpRefId, channel:'1', state:'24'})
    });
    var j=await r.json();
    if(j&&j.data&&j.data.status===0){
      DMT.txnResult=j.data.data||{};
      dmtRenderSuccess();
    } else {
      toast((j&&j.data&&j.data.message)||'Could not complete transfer','e');
    }
  }catch(e){
    toast('Network error — could not reach server','e');
  }finally{
    if(btn){ btn.disabled=false; btn.textContent='Confirm Transfer →'; }
  }
}

function dmtRenderSuccess(){
  var root=dmtRoot(); if(!root) return;
  var t=DMT.txnResult||{};
  var bene=DMT._beneInfo||{};
  var now=new Date();
  function pad(n){return String(n).padStart(2,'0');}
  var dateStr=pad(now.getDate())+' '+now.toLocaleString('en-IN',{month:'short'})+' '+now.getFullYear()+' '+pad(now.getHours())+':'+pad(now.getMinutes())+':'+pad(now.getSeconds());
  var rows=[
    ['Beneficiary',bene.name||''],
    ['Account',bene.account||''],
    ['Bank',bene.bank||''],
    ['IFSC',bene.ifsc||''],
    ['Transfer Amount','₹'+fmtN(DMT.amount)],
    ['Remarks',DMT.remarks||''],
    ['TXN ID',t.tid||t.txn_id||'—'],
    ['Bank Ref',t.bank_ref_num||'—'],
    ['Date & Time',dateStr],
  ];
  root.innerHTML =
    '<div style="background:var(--bg3);border:1px solid var(--green);border-radius:14px;padding:16px">'
    +'<div style="text-align:center;margin-bottom:12px"><div style="font-size:1.8rem">✅</div>'
    +'<div style="font-family:var(--font-head);font-size:.95rem;font-weight:700;color:var(--green)">Transfer Successful!</div>'
    +'<div style="font-size:.68rem;color:var(--rtai);margin-top:2px">🛡️ NPCI DMT via Eko</div></div>'
    +'<div style="background:var(--bg2);border-radius:10px;padding:10px;margin-bottom:10px">'
    +rows.map(function(r){
      return '<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--border);font-size:.76rem">'
        +'<span style="color:var(--muted2)">'+r[0]+'</span>'
        +'<span style="color:var(--text);font-weight:600;text-align:right;max-width:55%">'+r[1]+'</span></div>';
    }).join('')
    +'</div>'
    +'<button onclick="renderDMT()" style="width:100%;padding:9px;border-radius:9px;background:linear-gradient(135deg,var(--blue),var(--cyan));border:none;color:#fff;cursor:pointer;font-size:.82rem;font-weight:700">New Transfer</button>'
    +'</div>';
  toast('₹'+fmtN(DMT.amount)+' sent to '+(bene.name||'')+'! ✅','s');
}"""

content = content[:start_idx] + new_block + content[end_idx:]

backup = FILE + ".bak." + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
shutil.copy(FILE, backup)
with open(FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"✅ DMT rewired to real Eko flow in {FILE}")
print(f"   Backup of the previous version saved as {backup}")
