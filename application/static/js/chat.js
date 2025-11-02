// chat.js
// Exposes window.initChat() which wires up the chat form inside the
// injected chat panel. This allows the client router to fetch bot.html via AJAX
// and then call initChat() to (re)attach handlers.

window.initChat = function initChat() {
  console.log('initChat called');
  const form = document.getElementById('chat-form');
  const messages = document.getElementById('messages');
  const input = document.getElementById('message-input');
  if (!form || !messages || !input) {
    console.log('Missing elements:', {form, messages, input});
    return;
  }

  function escapeHtml(s){ return String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;'); }

  function appendMessage(kind, text){
    const wrapper = document.createElement('div');
    wrapper.className = 'message ' + kind;
    
    const bubble = document.createElement('div');
    bubble.className = 'bubble ' + kind;
    bubble.innerHTML = escapeHtml(text);
    
    if(kind === 'assistant'){
      const img = document.createElement('img');
      img.src = '/img/kjellOne.png';
      img.className = 'avatar';
      img.alt = 'Kjell AI';
      wrapper.appendChild(img);
      wrapper.appendChild(bubble);
    } else if(kind === 'user'){
      wrapper.appendChild(bubble);
      const img = document.createElement('img');
      img.src = '/img/userIcon2.png';
      img.className = 'avatar';
      img.alt = 'User';
      wrapper.appendChild(img);
    } else {
      wrapper.appendChild(bubble);
    }

    // TTS removed

    messages.appendChild(wrapper);
    messages.scrollTop = messages.scrollHeight;
    return wrapper; // Return the wrapper for later modification
  }

  // Remove any previously attached listener by cloning
  const newForm = form.cloneNode(true);
  form.parentNode.replaceChild(newForm, form);

  // Update references to the new elements
  const newInput = newForm.querySelector('#message-input');

  newForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = newInput.value.trim();
    console.log('Form submitted with text:', text);
    if(!text) return;
    appendMessage('user', text);
    newInput.value = '';

    //loading indicator
    const loadingWrapper = appendMessage('loading', 'AI is thinking...');
    const loadingBubble = loadingWrapper.querySelector('.bubble');

    try{
      const formData = new FormData();
      formData.append('message', text);
      const res = await fetch(window.location.pathname || '/bot', {
        method: 'POST',
        body: formData
      });
      if(res.ok){
        const data = await res.json();
        // Replace loading with response
        loadingWrapper.className = 'message assistant';
        loadingBubble.className = 'bubble assistant';
        loadingBubble.innerHTML = escapeHtml(data.reply || '(no reply)');
        // Add avatar for assistant
        const img = document.createElement('img');
        img.src = '/img/kjellOne.png';
        img.className = 'avatar';
        img.alt = 'Kjell AI';
        loadingWrapper.insertBefore(img, loadingWrapper.firstChild);
        // Auto-play TTS for assistant response
        const formData = new FormData();
        formData.append('text', data.reply);
        fetch('/tts', {
          method: 'POST',
          body: formData
        }).then(res => {
          if (!res.ok) {
            return res.text().then(text => { throw new Error(text); });
          }
          return res.blob();
        }).then(blob => {
          const audioUrl = URL.createObjectURL(blob);
          const audio = new Audio(audioUrl);
          audio.play();
          audio.onended = () => URL.revokeObjectURL(audioUrl);
        }).catch(err => console.warn('TTS failed:', err));
        messages.scrollTop = messages.scrollHeight;
      } else {
        // Replace with error
        loadingWrapper.className = 'message assistant';
        loadingBubble.className = 'bubble assistant';
        loadingBubble.innerHTML = escapeHtml('(error from server)');
        messages.scrollTop = messages.scrollHeight;
      }
    } catch (err) {
      // Replace with network error
      loadingWrapper.className = 'message assistant';
      loadingBubble.className = 'bubble assistant';
      loadingBubble.innerHTML = escapeHtml('(network error)');
      messages.scrollTop = messages.scrollHeight;
    }
  });

  // focus input
  newInput.focus();
};
