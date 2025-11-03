// cookies.js - Cookie consent banner functionality
(function(){
    function readCookie(name){
        const m = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
        return m ? decodeURIComponent(m[1]) : null;
    }

    function showBanner(){
        const b = document.getElementById('cookie-banner');
        if(b) b.style.display = 'block';
        return b;
    }

    const consent = readCookie('consent');
    if(consent !== 'true' && consent !== 'false'){
        const b = showBanner();
        const acceptBtn = document.getElementById('accept-cookies');
        const declineBtn = document.getElementById('decline-cookies');

        if(acceptBtn){
            acceptBtn.addEventListener('click', async function(){
                // immediately set a client-visible consent cookie so UI updates
                document.cookie = 'consent=true; path=/';
                if(b) b.style.display='none';
                // then notify server so it can create the httponly user_id and record in DB
                try{
                    await fetch('/accept_cookies', { method: 'GET', credentials: 'same-origin' });
                }catch(e){
                    console.warn('accept_cookies failed', e);
                }
            });
        }

        if(declineBtn){
            declineBtn.addEventListener('click', async function(){
                document.cookie = 'consent=false; path=/';
                if(b) b.style.display='none';
                try{
                    await fetch('/decline_cookies', { method: 'GET', credentials: 'same-origin' });
                }catch(e){
                    console.warn('decline_cookies failed', e);
                }
            });
        }
    }
})();