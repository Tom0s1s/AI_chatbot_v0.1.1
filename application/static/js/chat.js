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
    wrapper.appendChild(bubble);
    messages.appendChild(wrapper);
    messages.scrollTop = messages.scrollHeight;
    return wrapper; // Return the wrapper for later modification
  }

  // Remove any previously attached listener by cloning
  const newForm = form.cloneNode(true);
  form.parentNode.replaceChild(newForm, form);

  // Update references to the new elements
  const newInput = newForm.querySelector('#message-input');
  const newRecordBtn = newForm.querySelector('#record-btn');

  newForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = newInput.value.trim();
    console.log('Form submitted with text:', text);
    if(!text) return;
    appendMessage('user', text);
    newInput.value = '';

    // Add loading indicator
    const loadingWrapper = appendMessage('loading', 'AI is thinking...');
    const loadingBubble = loadingWrapper.querySelector('.bubble');

    try{
      const res = await fetch(window.location.pathname || '/bot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ message: text })
      });
      if(res.ok){
        const data = await res.json();
        // Replace loading with response
        loadingWrapper.className = 'message assistant';
        loadingBubble.className = 'bubble assistant';
        loadingBubble.innerHTML = escapeHtml(data.reply || '(no reply)');
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

  // --- Recording support (MediaRecorder) ---
  const recordBtn = newRecordBtn;
  let mediaStream = null;
  let recorder = null;
  let chunks = [];
  let isRecording = false;

  async function startRecording(){
    try{
      mediaStream = await navigator.mediaDevices.getUserMedia({audio:true});
      recorder = new MediaRecorder(mediaStream);
      chunks = [];
      recorder.ondataavailable = (ev) => { if(ev.data && ev.data.size) chunks.push(ev.data); };
      recorder.onstop = () => {
        const blob = new Blob(chunks, {type: 'audio/webm'});
        // make available for later sending to your TTS LLM
        window.lastRecordedAudio = blob;
        appendMessage('user', '[Voice message recorded]');
        // stop all tracks
        mediaStream.getTracks().forEach(t => t.stop());
        mediaStream = null; recorder = null; chunks = []; isRecording = false;
        recordBtn.classList.remove('recording');
        recordBtn.innerHTML = `<!-- mic icon -->\n          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">\n            <path d=\"M12 14a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v5a3 3 0 0 0 3 3z\" stroke=\"#0b1220\" stroke-width=\"1.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>\n            <path d=\"M19 11v1a7 7 0 0 1-14 0v-1\" stroke=\"#0b1220\" stroke-width=\"1.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>\n            <path d=\"M12 21v-3\" stroke=\"#0b1220\" stroke-width=\"1.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>\n          </svg>`;
      };
      recorder.start();
      isRecording = true;
      recordBtn.classList.add('recording');
      // show a visual indicator while recording
      recordBtn.innerHTML = '<span class="dot"></span>';
    } catch(err){
      console.warn('Microphone access denied or not available', err);
      alert('Unable to access microphone. Please check permissions.');
    }
  }

  function stopRecording(){
    if(recorder && recorder.state !== 'inactive') recorder.stop();
    // recorder.onstop will handle cleanup
  }

  if(recordBtn){
    recordBtn.addEventListener('click', (e)=>{
      e.preventDefault();
      if(isRecording){
        stopRecording();
      } else {
        startRecording();
      }
    });
  }
};
