// user.js - Current user info display
(async function(){
    try{
        const res = await fetch('/current_user', { credentials: 'same-origin' });
        if(!res.ok) return;
        const j = await res.json();
        if(!j || !j.user) return;
        const el = document.getElementById('current-user');
        if(!el) return;
        const short = j.user.short || j.user.id || '';
        const info = j.user.info || '';
        el.textContent = `User: ${short}${info ? ' — ' + info : ''}`;
    }catch(e){
        // silent fail; not critical
        console.debug('current_user fetch failed', e);
    }
})();