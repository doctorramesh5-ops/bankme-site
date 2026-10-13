import os,sys,shutil,time
f='app.html'
if not os.path.exists(f): sys.exit('Run this inside ~/Desktop/bankme-site')
s=open(f).read()
if 'UPGRADE_WEB_V1' in s: print('Already applied.'); sys.exit(0)
if s.count('</body>')<1 or 'function openService(' not in s: sys.exit('Anchors not found - nothing changed.')
JS=r'''
<script>
/* UPGRADE_WEB_V1 */
(function(){
  var BASE='https://bankme-backend.onrender.com';
  function isCust(){ try{ return typeof CU!=='undefined' && CU && (!CU.role || CU.role==='customer'); }catch(e){return false;} }
  function locked(svc){ return svc && /aeps|money transfer|dmt|domestic money/i.test((svc.name||'')+' '+(svc.id||'')); }
  /* 1. keep CU.role fresh from server replies */
  var _f=window.fetch;
  window.fetch=function(){
    var p=_f.apply(this,arguments);
    try{
      var u=String(arguments[0]&&arguments[0].url||arguments[0]||'');
      if(/\/user\/[^\/]+\/(kyc-status|balance)/.test(u)){
        p.then(function(r){ return r.clone().json(); }).then(function(d){
          if(d && d.role && typeof CU!=='undefined' && CU){ if(CU.role!==d.role){ CU.role=d.role; } }
        }).catch(function(){});
      }
    }catch(e){}
    return p;
  };
  /* 2. lock AEPS / DMT for customers */
  function upgradeModal(name){
    var o=document.createElement('div');
    o.style.cssText='position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,.85);display:flex;align-items:center;justify-content:center;padding:20px';
    o.onclick=function(e){ if(e.target===o) o.remove(); };
    var c=document.createElement('div');
    c.style.cssText='background:var(--bg2);border:1px solid rgba(245,158,11,.4);border-radius:18px;padding:26px 22px;max-width:340px;width:100%;text-align:center';
    c.innerHTML='<div style="font-size:2.2rem;margin-bottom:8px">🔒</div><div style="font-size:1rem;font-weight:800;color:var(--gold);margin-bottom:8px">Retailer account needed</div><div style="font-size:.78rem;color:var(--muted2);line-height:1.6;margin-bottom:16px"></div>';
    c.children[2].textContent=name+' is available for retailers. Open Profile, add your shop details and request a Retailer upgrade. Our team will approve it.';
    var b=document.createElement('button'); b.className='btn-primary'; b.textContent='Go to Profile →';
    b.onclick=function(){ o.remove(); try{ goPage('profile'); }catch(e){} };
    var x=document.createElement('button'); x.className='btn-outline'; x.style.marginTop='8px'; x.textContent='Close'; x.onclick=function(){ o.remove(); };
    c.appendChild(b); c.appendChild(x); o.appendChild(c); document.body.appendChild(o);
  }
  var _open=window.openService;
  window.openService=function(id){
    try{
      var svc=(typeof SERVICES!=='undefined')?SERVICES.find(function(s){return s.id===id;}):null;
      if(isCust() && locked(svc)){ upgradeModal(svc.name); return; }
    }catch(e){}
    return _open.apply(this,arguments);
  };
  /* 3. Upgrade card in Profile for customers */
  function esc(t){ var d=document.createElement('div'); d.textContent=t==null?'':t; return d.innerHTML; }
  function build(card){
    var wrap=document.createElement('div');
    wrap.className='pcard'; wrap.setAttribute('data-upg','1'); wrap.style.marginBottom='14px';
    wrap.innerHTML='<div style="font-family:var(--font-head);font-size:.9rem;font-weight:700;margin-bottom:6px">⬆️ Upgrade to Retailer</div>'
      +'<div style="font-size:.78rem;color:var(--muted2);line-height:1.6;margin-bottom:10px">AEPS and Money Transfer are for retailers. Complete your shop details below (name, address, location, shop front photo), then request the upgrade. Our team will check and approve.</div>'
      +'<div id="upg-status" style="font-size:.8rem;margin-bottom:10px;color:var(--muted2)">Checking status…</div>'
      +'<button class="btn-primary" id="upg-btn" style="width:100%">Request Retailer Upgrade →</button>';
    card.parentNode.insertBefore(wrap,card);
    var st=wrap.querySelector('#upg-status'), btn=wrap.querySelector('#upg-btn');
    function show(d){
      var s=(d&&(d.status||(d.request&&d.request.status)))||'';
      if(s==='pending'){ st.innerHTML='⏳ <b>Request submitted.</b> Waiting for approval.'; btn.style.display='none'; }
      else if(s==='approved'){ st.innerHTML='✅ <b>Approved.</b> Sign out and sign in again to see AEPS and Money Transfer.'; btn.style.display='none'; }
      else if(s==='rejected'){ st.innerHTML='❌ Rejected'+((d.reason||(d.request&&d.request.reason))?': '+esc(d.reason||d.request.reason):'')+'. Fix the details and request again.'; btn.style.display=''; }
      else { st.textContent='Not requested yet.'; btn.style.display=''; }
    }
    authFetch(BASE+'/upgrade/status').then(function(r){return r.json();}).then(show).catch(function(){ st.textContent='Status not available right now.'; });
    btn.onclick=function(){
      btn.disabled=true; btn.textContent='Sending…';
      authFetch(BASE+'/upgrade/request',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'})
        .then(function(r){return r.json();}).then(function(d){
          btn.disabled=false; btn.textContent='Request Retailer Upgrade →';
          if(d&&d.success){ show({status:'pending'}); }
          else { st.innerHTML='⚠️ '+esc((d&&(d.message||d.error))||'Could not send request'); }
        }).catch(function(){ btn.disabled=false; btn.textContent='Request Retailer Upgrade →'; st.textContent='Network error. Try again.'; });
    };
  }
  var t=null;
  function scan(){
    if(!isCust()) return;
    var cards=document.querySelectorAll('.pcard');
    for(var i=0;i<cards.length;i++){
      var c=cards[i];
      if(c.getAttribute('data-upg')) continue;
      if(c.textContent.indexOf('Shop Details')>-1 && c.querySelector('#shop-view')){
        if(c.previousElementSibling && c.previousElementSibling.getAttribute('data-upg')) continue;
        build(c); return;
      }
    }
  }
  new MutationObserver(function(){ clearTimeout(t); t=setTimeout(scan,250); }).observe(document.body,{childList:true,subtree:true});
})();
</script>
'''
shutil.copy(f,f+'.bak.'+time.strftime('%Y%m%d%H%M%S'))
k=s.rfind('</body>')
s=s[:k]+JS+s[k:]
open(f,'w').write(s); print('Applied OK.')
