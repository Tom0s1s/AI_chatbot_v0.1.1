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

    // Add speak button for assistant messages
    if(kind === 'assistant'){
      const speakBtn = document.createElement('button');
      speakBtn.className = 'speak-btn';
      speakBtn.textContent = '🔊';
      speakBtn.title = 'Speak this message';
      speakBtn.addEventListener('click', () => {
        const formData = new FormData();
        formData.append('text', text);
        fetch('/tts', {
          method: 'POST',
          body: formData
        }).then(res => res.blob()).then(blob => {
          const audioUrl = URL.createObjectURL(blob);
          const audio = new Audio(audioUrl);
          audio.play();
          audio.onended = () => URL.revokeObjectURL(audioUrl);
        }).catch(err => console.warn('TTS failed:', err));
      });
      wrapper.appendChild(speakBtn);
    }

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

    //loading indicator
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
        // Auto-play TTS for assistant response
        const formData = new FormData();
        formData.append('text', data.reply);
        fetch('/tts', {
          method: 'POST',
          body: formData
        }).then(res => res.blob()).then(blob => {
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

  // --- Recording support (WAV using Web Audio API) ---
  const recordBtn = newRecordBtn;
  let audioContext = null;
  let source = null;
  let processor = null;
  let samples = [];
  let isRecording = false;

  function encodeWAV(samples, sampleRate) {
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);
    const writeString = (offset, string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    };
    writeString(0, 'RIFF');
    view.setUint32(4, 36 + samples.length * 2, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true); // PCM
    view.setUint16(22, 1, true); // mono
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(36, 'data');
    view.setUint32(40, samples.length * 2, true);
    for (let i = 0; i < samples.length; i++) {
      view.setInt16(44 + i * 2, samples[i] * 0x7FFF, true);
    }
    return buffer;
  }

  async function startRecording(){
    try{
      const stream = await navigator.mediaDevices.getUserMedia({audio:true});
      audioContext = new AudioContext();
      source = audioContext.createMediaStreamSource(stream);
      processor = audioContext.createScriptProcessor(4096, 1, 1);
      samples = [];
      processor.onaudioprocess = (e) => {
        const inputBuffer = e.inputBuffer.getChannelData(0);
        for (let i = 0; i < inputBuffer.length; i++) {
          samples.push(inputBuffer[i]);
        }
      };
      source.connect(processor);
      processor.connect(audioContext.destination);
      isRecording = true;
      recordBtn.classList.add('recording');
      recordBtn.innerHTML = '<span class="dot"></span>';
    } catch(err){
      console.warn('Microphone access denied or not available', err);
      alert('Unable to access microphone. Please check permissions.');
    }
  }

  function stopRecording(){
    if (source) source.disconnect();
    if (processor) processor.disconnect();
    if (audioContext) audioContext.close();
    const wavBuffer = encodeWAV(samples, audioContext.sampleRate);
    const blob = new Blob([wavBuffer], {type: 'audio/wav'});
    // Send audio to server
    const formData = new FormData();
    formData.append('audio', blob, 'recording.wav');

    // Add loading for audio processing
    const loadingWrapper = appendMessage('loading', 'Processing audio...');
    const loadingBubble = loadingWrapper.querySelector('.bubble');

    fetch(window.location.pathname || '/bot', {
      method: 'POST',
      body: formData
    }).then(res => res.json()).then(data => {
      // Replace with transcription or response
      loadingWrapper.className = 'message assistant';
      loadingBubble.className = 'bubble assistant';
      loadingBubble.innerHTML = escapeHtml(data.reply || '(no reply)');
      messages.scrollTop = messages.scrollHeight;
    }).catch(err => {
      loadingWrapper.className = 'message assistant';
      loadingBubble.className = 'bubble assistant';
      loadingBubble.innerHTML = escapeHtml('(audio processing error)');
      messages.scrollTop = messages.scrollHeight;
    });

    // Reset
    audioContext = null; source = null; processor = null; samples = []; isRecording = false;
    recordBtn.classList.remove('recording');
    recordBtn.innerHTML = `<!-- mic icon -->\n          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">\n            <path d=\"M12 14a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v5a3 3 0 0 0 3 3z\" stroke=\"#0b1220\" stroke-width=\"1.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>\n            <path d=\"M19 11v1a7 7 0 0 1-14 0v-1\" stroke=\"#0b1220\" stroke-width=\"1.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>\n            <path d=\"M12 21v-3\" stroke=\"#0b1220\" stroke-width=\"1.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>\n          </svg>`;
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
