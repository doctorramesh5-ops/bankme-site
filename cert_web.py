import os,sys,shutil,time
f='app.html'
if not os.path.exists(f): sys.exit('Run this inside ~/Desktop/bankme-site')
s=open(f).read()
if 'CERT_WEB_V1' in s: print('Already applied.'); sys.exit(0)
if s.count('</body>')<1 or '🏪 Shop Details' not in s: sys.exit('Anchors not found - nothing changed.')
JS='''
<script>
/* CERT_WEB_V1 */
(function(){
  function biz(){ try{ return typeof CU!=='undefined' && CU && ['retailer','distributor','superdist'].indexOf(CU.role)>=0; }catch(e){return false;} }
  var t=null;
  function scan(){
    if(!biz()) return;
    var cards=document.querySelectorAll('.pcard');
    for(var i=0;i<cards.length;i++){
      var c=cards[i];
      if(c.getAttribute('data-cert')) continue;
      if(c.textContent.indexOf('Shop Details')>-1 && c.querySelector('#shop-view')){
        if(c.nextElementSibling && c.nextElementSibling.getAttribute('data-cert')) continue;
        var w=document.createElement('div'); w.className='pcard'; w.setAttribute('data-cert','1'); w.style.marginBottom='14px';
        var h=document.createElement('div'); h.style.cssText='font-family:var(--font-head);font-size:.9rem;font-weight:700;margin-bottom:6px'; h.textContent='🏅 Authorised BankMe Certificate'; w.appendChild(h);
        var p=document.createElement('div'); p.style.cssText='font-size:.78rem;color:var(--muted2);line-height:1.6;margin-bottom:10px'; p.textContent='Print this certificate in high quality and display it at your shop. It has your Network ID and a QR code customers can scan to verify you.'; w.appendChild(p);
        var b=document.createElement('button'); b.className='btn-primary'; b.style.width='100%'; b.textContent='Open Certificate →';
        b.onclick=function(){ window.open('/certificate.html','_blank'); };
        w.appendChild(b);
        c.parentNode.insertBefore(w,c.nextSibling); return;
      }
    }
  }
  new MutationObserver(function(){ clearTimeout(t); t=setTimeout(scan,250); }).observe(document.body,{childList:true,subtree:true});
})();
</script>
'''
shutil.copy(f,f+'.bak.'+time.strftime('%Y%m%d%H%M%S'))
k=s.rfind('</body>'); s=s[:k]+JS+s[k:]
open(f,'w').write(s); print('Applied OK.')
