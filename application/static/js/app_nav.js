// app_nav.js
// Intercept internal link clicks, fetch the target page, extract the
// <main> content and replace it without a full reload. Maintain history state
// and call page-specific init functions (like window.initChat).

(function(){
  const rootMainSelector = 'main';

  function isInternalLink(anchor){
    return location.origin === anchor.origin && anchor.pathname;
  }

  // Duration should match the CSS transition in index_style.css
  const TRANSITION_MS = 220;

  async function loadUrl(url, addHistory=true){
    try{
      const res = await fetch(url, {headers:{'X-Requested-With':'XMLHttpRequest'}});
      const text = await res.text();
      const parser = new DOMParser();
      const doc = parser.parseFromString(text, 'text/html');
      const newMain = doc.querySelector(rootMainSelector);
      if(!newMain){
        window.location.href = url; // fallback
        return;
      }

      const currMain = document.querySelector(rootMainSelector);
      if(!currMain){
        // nothing to swap into, just navigate
        window.location.href = url;
        return;
      }

      // Start fade-out
      currMain.classList.remove('fade-in');
      currMain.classList.add('fade-out');

      // Wait for transitionend or fallback timeout
      await new Promise((resolve) => {
        let done = false;
        const onEnd = (e) => {
          if (e && e.target !== currMain) return;
          if (done) return; done = true;
          currMain.removeEventListener('transitionend', onEnd);
          resolve();
        };
        currMain.addEventListener('transitionend', onEnd);
        setTimeout(() => onEnd(), TRANSITION_MS + 30);
      });

      // Replace content
      currMain.innerHTML = newMain.innerHTML;

      // Force reflow then fade in
      // eslint-disable-next-line no-unused-expressions
      currMain.offsetHeight;
      currMain.classList.remove('fade-out');
      currMain.classList.add('fade-in');

      // run route-specific init
      runInitForPath(url);

      if(addHistory){
        history.pushState({path:url}, '', url);
      }
    } catch (err){
      console.error('Navigation error', err);
      window.location.href = url;
    }
  }

  function runInitForPath(url){
    try{
      const path = new URL(url, location.origin).pathname;
      if(path.startsWith('/bot')){
        console.log('Calling initChat for /bot');
        if(window.initChat) window.initChat();
      }
      if(path.startsWith('/info')){
        if(window.initInfo) window.initInfo();
      }
      if(path.startsWith('/admin')){
        if(window.initAdmin) window.initAdmin();
      }
      // add other route-specific initializers here
    } catch(e){}
  }

  // delegate clicks on anchor tags
  document.addEventListener('click', (e)=>{
    const a = e.target.closest('a');
    if(!a) return;
    if(a.hasAttribute('data-no-ajax')) return; // opt-out
    if(isInternalLink(a)){
      e.preventDefault();
      loadUrl(a.href);
    }
  });

  // handle back/forward
  window.addEventListener('popstate', (e)=>{
    const path = (e.state && e.state.path) || location.pathname;
    loadUrl(path, false);
  });

  // init: if current path is bot, call chat init
  document.addEventListener('DOMContentLoaded', ()=>{
    runInitForPath(location.href);
  });
})();
