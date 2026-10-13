import os,sys,shutil,time
f='app.html'
if not os.path.exists(f): sys.exit('Run this inside ~/Desktop/bankme-site')
s=open(f).read()
if 'CARDWD_WEB_V1' in s: print('Already applied.'); sys.exit(0)
if 'function initCreditCard(' not in s or s.count('</body>')<1: sys.exit('Anchors not found - nothing changed.')
JS='''
<script>
/* CARDWD_WEB_V1 */
(function(){
  var orig=window.initCreditCard;
  window.initCreditCard=function(){
    var root=document.getElementById('creditcard-root');
    fetch('https://bankme-backend.onrender.com/cardwd/status').then(function(r){return r.json();}).then(function(d){
      if(d && d.enabled){ orig.apply(null,[]); }
      else if(root){ root.innerHTML='<div style="text-align:center;padding:36px 16px"><div style="font-size:2.4rem">🚀</div><div style="font-weight:800;font-size:1rem;margin:8px 0">Launching soon</div><div style="font-size:.8rem;color:var(--muted2);line-height:1.6">Card Withdrawal is being activated. We will let you know when it is ready.</div></div>'; }
    }).catch(function(){
      if(root){ root.innerHTML='<div style="text-align:center;padding:30px;font-size:.8rem;color:var(--muted2)">Card Withdrawal is not available right now.</div>'; }
    });
  };
})();
</script>
'''
shutil.copy(f,f+'.bak.'+time.strftime('%Y%m%d%H%M%S'))
k=s.rfind('</body>'); s=s[:k]+JS+s[k:]
open(f,'w').write(s); print('Applied OK.')
