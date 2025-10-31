// admin.js
// Exposes window.initAdmin() which wires up the admin UI: user selector, export, clear, refresh.

window.initAdmin = function initAdmin(){
  const userSelect = document.getElementById('user-select');
  const refreshBtn = document.getElementById('refresh-logs');
  const exportBtn = document.getElementById('export-btn');
  const clearBtn = document.getElementById('clear-btn');

  async function loadUsers(){
    try{
      const res = await fetch('/admin/users');
      const data = await res.json();
      if(!userSelect) return;
      userSelect.innerHTML = '';
      data.forEach(u => {
        const opt = document.createElement('option');
        opt.value = u.id;
        opt.textContent = u.id + (u.info ? (' — ' + u.info) : '');
        userSelect.appendChild(opt);
      });
      // if there's a query param user_id, try to select it
      const params = new URLSearchParams(location.search);
      const sel = params.get('user_id');
      if(sel){ userSelect.value = sel; }
    } catch(e){ console.error('Failed to load users', e); }
  }

  async function refreshLogs(userId){
    try{
      const url = userId ? `/admin?user_id=${encodeURIComponent(userId)}` : '/admin';
      const res = await fetch(url, {headers:{'X-Requested-With':'XMLHttpRequest'}});
      const text = await res.text();
      const parser = new DOMParser();
      const doc = parser.parseFromString(text, 'text/html');
      const newMain = doc.querySelector('main');
      if(newMain){ document.querySelector('main').innerHTML = newMain.innerHTML; }
      // re-run admin init (rebind) after replacing content
      if(window.initAdmin) window.initAdmin();
    } catch(e){ console.error(e); }
  }

  if(userSelect){
    userSelect.addEventListener('change', ()=>{
      const uid = userSelect.value;
      // push to history and refresh main
      history.pushState({path:`/admin?user_id=${uid}`}, '', `/admin?user_id=${encodeURIComponent(uid)}`);
      refreshLogs(uid);
    });
  }

  if(refreshBtn){ refreshBtn.addEventListener('click', ()=> refreshLogs(userSelect?.value)); }

  if(exportBtn){
    exportBtn.addEventListener('click', ()=>{
      const uid = userSelect?.value;
      const url = uid ? `/admin/export?user_id=${encodeURIComponent(uid)}` : '/admin/export';
      window.open(url, '_blank');
    });
  }

  if(clearBtn){
    clearBtn.addEventListener('click', async ()=>{
      const uid = userSelect?.value;
      if(!uid) return alert('Select a user first');
      if(!confirm('Clear all events for user ' + uid + '? This cannot be undone.')) return;
      try{
        const res = await fetch('/admin/clear', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({user_id: uid})});
        const data = await res.json();
        if(data.ok){
          alert('Events cleared');
          refreshLogs(uid);
        } else alert('Failed: ' + (data.error || 'unknown'));
      } catch(e){ console.error(e); alert('Request failed'); }
    });
  }

  // initial load
  loadUsers();
};
