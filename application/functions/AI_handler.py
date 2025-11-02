import os
from typing import Optional, Dict, Any
import ollama
import logging
from . import db_handler

class AIHandler:
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self.default_chat_model = (
            self.config.get("default_model")
            or self.config.get("default_chat_model")
            or os.environ.get("OLLAMA_CHAT_MODEL")
            or "llama2:7b"
        )
        self.default_reason_model = (
            self.config.get("default_reason_model")
            or os.environ.get("OLLAMA_REASON_MODEL")
            or "phi4-reasoning:14b"
        )

    def _run_ollama(self, model: str, messages) -> dict:
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        try:
            response = ollama.chat(model=model, messages=messages)
            return {"text": response["message"]["content"]}
        except Exception as e:
            return {"text": f"(Ollama error: {e})"}

    def status(self) -> dict:
        return {
            "default_model": self.default_chat_model,
            "default_reason_model": self.default_reason_model,
        }

    def chat(self, prompt: str, model: str = None) -> dict:
        model_to_use = model or self.default_chat_model
        return self._run_ollama(model_to_use, prompt)

    def reason(self, prompt: str, model: str = None) -> dict:
        model_to_use = model or self.default_reason_model
        return self._run_ollama(model_to_use, prompt)

    def caption_image(self, img_bytes: bytes) -> str:
        try:
            import base64
            img_b64 = base64.b64encode(img_bytes).decode('utf-8')
            messages = [
                {
                    "role": "user",
                    "content": f"Describe this image in detail: data:image/jpeg;base64,{img_b64}"
                }
            ]
            response = ollama.chat(model="llava:13b", messages=messages)
            return response["message"]["content"]
        except Exception as e:
            return f"(Image captioning failed: {e})"

    def transcribe_audio(self, audio_bytes: bytes) -> str:
        try:
            import tempfile
            import whisper
            model = whisper.load_model("base")
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name
            
            result = model.transcribe(temp_path)
            import os
            os.unlink(temp_path)
            return result["text"].strip()
        except Exception as e:
            return f"(Transcription failed: {e})"

    def handle_bot_request(self, request, user_id):
        user_message = None

        # 1) Audio
        audio_file = request.files.get('audio')
        transcription = None
        if audio_file:
            audio_bytes = audio_file.read()
            transcription = self.transcribe_audio(audio_bytes)

        # 2) Image
        image_file = request.files.get('image')
        image_caption = None
        if image_file:
            img_bytes = image_file.read()
            image_caption = self.caption_image(img_bytes)

        # 3) Text
        if not user_message:
            user_message = request.form.get("message") or transcription

        if not user_message and not image_caption:
            return {"error": "Ingen input mottagen"}

        # Logga användarens input
        logged_input = user_message or f"[image only] caption:{image_caption}"
        db_handler.add_event(user_id, "chat_user", logged_input)

        # Hämta tidigare konversation
        events = db_handler.get_events(user_id, limit=20)[::-1]
        messages = [{"role": "system", "content":"Your name is Kjell, you are a wise and friendly medieval knight, an all-knowing AI assistant who helps users with their questions."}]
        for event_type, content, _ in events:
            if event_type == "chat_user":
                messages.append({"role": "user", "content": content})
            elif event_type == "chat_llm":
                messages.append({"role": "assistant", "content": content})

        if user_message:
            messages.append({"role": "user", "content": user_message})
        if image_caption:
            messages.append({"role": "user", "content": f"[Image description]: {image_caption}"})

        model = request.form.get('model') or self.default_chat_model
        try:
            response = ollama.chat(model=model, messages=messages)
            assistant_reply = response["message"]["content"]
        except Exception as e:
            logging.exception("LLM chat failed: %s", e)
            assistant_reply = f"(Fallback) You said: {user_message or '[image]'}"

        db_handler.add_event(user_id, "chat_llm", assistant_reply)
        return {"reply": assistant_reply}
