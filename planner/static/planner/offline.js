(function(){
  const KEY='workflow-offline-queue-v1';
  const read=()=>{try{return JSON.parse(localStorage.getItem(KEY)||'[]')}catch(e){return[]}};
  const write=v=>localStorage.setItem(KEY,JSON.stringify(v));
  const notify=msg=>{if('Notification'in window&&Notification.permission==='granted')new Notification('WorkFlow Planner',{body:msg,icon:'/static/planner/icon.svg'});};
  const banner=msg=>{let el=document.getElementById('offline-status');if(!el){el=document.createElement('div');el.id='offline-status';el.style='position:fixed;left:14px;right:14px;bottom:14px;z-index:30;padding:11px 14px;border-radius:9px;background:#172033;color:#fff;font:600 12px system-ui;box-shadow:0 8px 22px #17203333';document.body.appendChild(el)}el.textContent=msg;el.hidden=false;setTimeout(()=>el.hidden=true,4500)};
  const sync=async()=>{const items=read();if(!items.length||!navigator.onLine)return;try{const r=await fetch('/sync/offline/',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(items)});if(r.ok){localStorage.removeItem(KEY);banner('Offline changes synced.')}}catch(e){}};
  window.addEventListener('online',sync); if(!navigator.onLine)banner('Offline mode: changes will sync when online.'); sync();
  document.querySelectorAll('form[data-offline-kind]').forEach(form=>form.addEventListener('submit',e=>{if(navigator.onLine)return;e.preventDefault();const fd=new FormData(form),item={kind:form.dataset.offlineKind,title:fd.get('title')||'',description:fd.get('description')||'',body:fd.get('body')||'',priority:fd.get('priority')||'MEDIUM'};if(!item.title){banner('Add a title before saving.');return}const items=read();items.push(item);write(items);const msg='Saved on this device. It will sync when online.';banner(msg);notify(item.kind==='note'?'Note saved locally.':'Task saved locally.');form.reset();}));
})();
