import os,sys,shutil,time
f='app.html'
if not os.path.exists(f): sys.exit('Run this inside ~/Desktop/bankme-site')
s=open(f).read()
if 'SIGNUP_WEB_V1' in s: print('Already applied.'); sys.exit(0)
if s.count('</body>')<1 or 'function doSignupStep1(' not in s or 'id="si-terms"' not in s: sys.exit('Anchors not found - nothing changed.')
JS=r'''
<script>
/* SIGNUP_WEB_V1 */
(function(){
  var ROLE_NAME={customer:'Customer',retailer:'Retailer',distributor:'Distributor',superdist:'Super Distributor',whitelabel:'White Label Partner'};
  /* DRAFT policy points - have your lawyer review and edit before launch */
  var POL={
    customer:{
      t:['You use BankMe for wallet top-up, payments, BBPS bill pay, travel, cards and payouts in your own name.',
         'AEPS and Money Transfer are not available to Customers. To use them, upgrade to Retailer with shop documents and wait for approval.',
         'KYC is mandatory. Payments must come from an account in your own name; payments from a mismatched name are blocked and returned.',
         'Misuse, fraud or third-party use can lead to account freeze and reporting to authorities as required by law.'],
      r:['A failed transaction where money was debited is reversed to your wallet or source account as per RBI/NPCI timelines.',
         'A successful transaction cannot be cancelled. Service charges and gateway fees already paid are not refundable.',
         'Top-ups blocked for name mismatch are refunded to the paying account automatically.',
         'Raise any dispute from the app (Help) with the transaction ID.']},
    retailer:{
      t:['You run a genuine shop and offer BankMe services (AEPS, Money Transfer, BBPS, recharge and more) to your own customers.',
         'Shop details, photos and location must be true. BankMe may verify them on site.',
         'You are responsible for customer consent, biometric capture and cash handling for each transaction.',
         'Commission is paid as per your plan and can be reversed for failed, disputed or fraudulent transactions.',
         'BankMe may suspend services for suspicious activity, as required by RBI/NPCI/partner rules.'],
      r:['Failed AEPS or Money Transfer transactions are reversed as per bank and partner timelines.',
         'Commission on a reversed or refunded transaction is deducted from your wallet.',
         'Verification and onboarding fees, if any, are not refundable once the service is activated.',
         'Chargebacks or customer disputes that are your responsibility are recovered from your wallet.']},
    distributor:{
      t:['You onboard and support retailers under you and are responsible for their genuine, compliant activity.',
         'KYC and shop verification of your retailers must be true and complete.',
         'Your commission depends on your retailers valid transactions and can be reversed with them.',
         'BankMe may change, pause or end the arrangement for fraud, non-compliance or inactivity.'],
      r:['Distributor commission on a refunded or reversed retailer transaction is reversed.',
         'Joining or onboarding fees, if any, are not refundable after activation.',
         'Wallet balance can be withdrawn to your verified bank account as per payout rules, after any pending dues.',
         'Disputes are handled through your BankMe relationship manager or support.']},
    superdist:{
      t:['You manage distributors and retailers in your region and are responsible for their onboarding quality.',
         'GST registration is required if your business turnover is above Rs 25 lakh.',
         'Your account stays pending until BankMe verifies your business documents.',
         'Commission and overrides are paid as per your agreement and are reversed on refunded or fraudulent transactions.',
         'BankMe may audit your network and suspend access for non-compliance.'],
      r:['Overrides on refunded or reversed transactions are deducted from your wallet.',
         'Onboarding or licence fees, if any, are not refundable after activation.',
         'Settlement and dues are handled as per your signed agreement with BankMe.',
         'Disputes go to BankMe business support with the transaction IDs.']},
    whitelabel:{
      t:['You run BankMe-powered services under your own brand through a registered business.',
         'A business above Rs 2 crore turnover must be an LLP or Private Limited company with valid registration.',
         'Your account stays pending until BankMe verifies your documents and signs an agreement with you.',
         'You are responsible for the compliance, customer support and conduct of everyone in your network.',
         'BankMe may audit, suspend or end the partnership for non-compliance, as required by RBI/NPCI/partner rules.'],
      r:['Refunds to your network users follow the same RBI/NPCI timelines; reversed amounts are adjusted in your wallet.',
         'Setup, licence or branding fees, if any, are as per your signed agreement and are not refundable after go-live.',
         'Revenue share on reversed or refunded transactions is deducted from your settlement.',
         'Commercial disputes are resolved as set out in your agreement with BankMe.']}
  };
  var $=function(i){return document.getElementById(i);};
  function role(){ return ($('si-role')||{}).value||'customer'; }
  function list(a){ return '<ul style="margin:6px 0 0 18px;padding:0">'+a.map(function(x){return '<li style="margin-bottom:6px">'+x+'</li>';}).join('')+'</ul>'; }
  window.showPolicyBox=function(kind){
    var r=role(), p=POL[r]||POL.customer;
    var o=document.createElement('div');
    o.style.cssText='position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,.85);display:flex;align-items:center;justify-content:center;padding:18px';
    o.onclick=function(e){ if(e.target===o) o.remove(); };
    var c=document.createElement('div');
    c.style.cssText='background:var(--bg2);border:1px solid var(--border2);border-radius:16px;padding:22px 20px;max-width:420px;width:100%;max-height:80vh;overflow:auto;font-size:.8rem;color:var(--text);line-height:1.5';
    c.innerHTML='<div style="font-weight:800;font-size:.95rem;margin-bottom:4px">'+(kind==='t'?'Terms &amp; Conditions':'Refund Policy')+' — '+ROLE_NAME[r]+'</div>'
      +'<div style="font-size:.7rem;color:var(--muted2);margin-bottom:6px">Key points. Full policy: <a href="https://bankme.co.in/'+(kind==='t'?'terms':'refund-policy')+'" target="_blank" style="color:var(--rtai)">bankme.co.in</a></div>'
      +list(p[kind]);
    var b=document.createElement('button'); b.className='btn-outline'; b.style.marginTop='14px'; b.textContent='Close'; b.onclick=function(){o.remove();};
    c.appendChild(b); o.appendChild(c); document.body.appendChild(o);
  };
  /* build UI */
  var old=$('si-terms'); if(!old) return;
  var oldLabel=old.closest('label'); if(oldLabel) oldLabel.style.display='none';
  var wl=$('wl-fields'); if(wl) wl.style.display='none';
  var box=document.createElement('div');
  box.id='biz-fields';
  box.innerHTML=
   '<div id="bz-sd" style="display:none;margin-top:8px;border:1px solid rgba(6,182,212,.3);background:rgba(6,182,212,.06);border-radius:10px;padding:12px">'
  +'<div style="font-size:.78rem;color:var(--cyan);font-weight:700;margin-bottom:8px">🏢 Business details</div>'
  +'<label class="flabel">Yearly business turnover</label>'
  +'<select class="fsel" id="bz-turn"></select>'
  +'<div id="bz-gstwrap"><label class="flabel" id="bz-numlbl">GSTIN</label>'
  +'<input class="finp" id="bz-num" maxlength="15" style="text-transform:uppercase" placeholder="15-character GSTIN"/></div>'
  +'<div id="bz-ctwrap" style="display:none"><label class="flabel">Company registration type</label>'
  +'<select class="fsel" id="bz-ctype"><option value="">-- Select --</option><option value="LLP">LLP (Limited Liability Partnership)</option><option value="PVT_LTD">Private Limited Company</option></select></div>'
  +'<div id="bz-note" style="font-size:.72rem;color:var(--muted2);line-height:1.5"></div></div>'
  +'<div style="margin:14px 0;display:flex;flex-direction:column;gap:9px">'
  +'<label style="display:flex;align-items:flex-start;gap:8px;cursor:pointer"><input type="checkbox" id="bz-t" style="margin-top:3px;flex-shrink:0"/><span style="font-size:.78rem;color:var(--muted2);line-height:1.4">I agree to the <a href="#" id="bz-tl" style="color:var(--rtai)">Terms &amp; Conditions for <span class="bz-rn"></span></a> and the <a href="https://bankme.co.in/privacy-policy" target="_blank" style="color:var(--rtai)">Privacy Policy</a></span></label>'
  +'<label style="display:flex;align-items:flex-start;gap:8px;cursor:pointer"><input type="checkbox" id="bz-r" style="margin-top:3px;flex-shrink:0"/><span style="font-size:.78rem;color:var(--muted2);line-height:1.4">I agree to the <a href="#" id="bz-rl" style="color:var(--rtai)">Refund Policy for <span class="bz-rn"></span></a></span></label></div>';
  var anchor=wl||old.closest('label');
  anchor.parentNode.insertBefore(box,(oldLabel||anchor));
  $('bz-tl').onclick=function(e){e.preventDefault();showPolicyBox('t');};
  $('bz-rl').onclick=function(e){e.preventDefault();showPolicyBox('r');};
  function sync(){ old.checked=$('bz-t').checked&&$('bz-r').checked; }
  $('bz-t').onchange=sync; $('bz-r').onchange=sync;
  function refresh(){
    var r=role();
    Array.prototype.forEach.call(document.querySelectorAll('.bz-rn'),function(e){e.textContent=ROLE_NAME[r]||'';});
    var sd=$('bz-sd'); var show=(r==='superdist'||r==='whitelabel');
    sd.style.display=show?'block':'none';
    var t=$('bz-turn');
    if(r==='superdist'){
      t.innerHTML='<option value="low">Up to ₹25 lakh</option><option value="high">Above ₹25 lakh</option>';
    } else if(r==='whitelabel'){
      t.innerHTML='<option value="low">Up to ₹2 crore</option><option value="high">Above ₹2 crore</option>';
    }
    if(wl) wl.style.display='none';
    turn();
    $('bz-t').checked=false; $('bz-r').checked=false; sync();
  }
  function turn(){
    var r=role(), hi=$('bz-turn').value==='high';
    if(r==='superdist'){
      $('bz-ctwrap').style.display='none';
      $('bz-numlbl').textContent=hi?'GSTIN (required)':'GSTIN (optional)';
      $('bz-note').textContent=hi?'GST registration is mandatory for a Super Distributor with business above ₹25 lakh.':'GST is optional up to ₹25 lakh. You can add it later.';
    } else if(r==='whitelabel'){
      $('bz-ctwrap').style.display='block';
      $('bz-numlbl').textContent=hi?'LLPIN / CIN (required)':'GSTIN / LLPIN / CIN';
      $('bz-note').textContent=hi?'Business above ₹2 crore must be an LLP or Private Limited company. Select the type and enter its registration number.':'Select your registration type and enter the number. Your account will be checked by BankMe before activation.';
    }
  }
  $('bz-turn').addEventListener('change',turn);
  $('si-role').addEventListener('change',refresh);
  refresh();
  /* validation wrapper */
  var _step=window.doSignupStep1;
  window.doSignupStep1=function(){
    var err=$('si-err'), r=role();
    sync();
    if(!$('bz-t').checked){ err.textContent='Please accept the Terms & Conditions for '+ROLE_NAME[r]; return; }
    if(!$('bz-r').checked){ err.textContent='Please accept the Refund Policy for '+ROLE_NAME[r]; return; }
    var ct=$('si-companytype'), num=$('si-gstnumber');
    if(ct) ct.innerHTML='<option value="">-- Select --</option><option value="GST">GST</option><option value="LLP">LLP</option><option value="PVT_LTD">PVT_LTD</option>';
    if(ct) ct.value=''; if(num) num.value='';
    if(r==='superdist'||r==='whitelabel'){
      var hi=$('bz-turn').value==='high', n=($('bz-num').value||'').trim().toUpperCase(), type='';
      if(r==='superdist'){
        type=n?'GST':'';
        if(hi && !/^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$/.test(n)){ err.textContent='Enter a valid 15-character GSTIN. GST is required above ₹25 lakh'; return; }
        if(n && !/^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$/.test(n)){ err.textContent='GSTIN is not valid'; return; }
      } else {
        type=$('bz-ctype').value;
        if(hi && type!=='LLP' && type!=='PVT_LTD'){ err.textContent='Above ₹2 crore, LLP or Private Limited registration is required'; return; }
        if(!type){ err.textContent='Select your company registration type'; return; }
        if(n.length<6){ err.textContent='Enter a valid registration number'; return; }
        if(type==='LLP' && !/^[A-Z]{3}-?[0-9]{4}$/.test(n) && n.length<6){ err.textContent='Enter a valid LLPIN'; return; }
        if(type==='PVT_LTD' && n.length!==21){ err.textContent='CIN must be 21 characters'; return; }
      }
      if(ct) ct.value=type; if(num) num.value=n;
    }
    return _step.apply(this,arguments);
  };
})();
</script>
'''
shutil.copy(f,f+'.bak.'+time.strftime('%Y%m%d%H%M%S'))
k=s.rfind('</body>')
s=s[:k]+JS+s[k:]
open(f,'w').write(s); print('Applied OK.')
