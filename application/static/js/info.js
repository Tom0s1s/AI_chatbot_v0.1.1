// info.js
// Provides window.initInfo() to initialize the Info page after AJAX injection.
// Stores the About and Project Summary in localStorage so you can edit them in-place.

(function(){
  const ABOUT_KEY = 'ai_chat_about_me';
  const PROJECT_KEY = 'ai_chat_project_summary';

  window.initInfo = function initInfo(){
    const aboutEl = document.getElementById('about-me');
    const projEl = document.getElementById('project-summary');
    const saveBtn = document.getElementById('save-summary');
    const clearBtn = document.getElementById('clear-summary');

    if(aboutEl){
      const savedAbout = localStorage.getItem(ABOUT_KEY);
      if(savedAbout) aboutEl.innerText = savedAbout;

      aboutEl.addEventListener('input', ()=>{
        // autosave small edits
        localStorage.setItem(ABOUT_KEY, aboutEl.innerText);
      });
    }

    if(projEl){
      const savedProj = localStorage.getItem(PROJECT_KEY);
      if(savedProj) projEl.value = savedProj;

      if(saveBtn){
        saveBtn.addEventListener('click', ()=>{
          localStorage.setItem(PROJECT_KEY, projEl.value);
          saveBtn.innerText = 'Saved';
          setTimeout(()=> saveBtn.innerText = 'Save', 1200);
        });
      }

      if(clearBtn){
        clearBtn.addEventListener('click', ()=>{
          projEl.value = '';
          localStorage.removeItem(PROJECT_KEY);
        });
      }
    }
  };
})();
