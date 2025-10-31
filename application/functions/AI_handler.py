import os
from typing import Optional, Dict, Any
import ollama

class AIHandler:
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Lightweight AI handler.

        Accepts an optional config dict with keys like:
          - default_model / default_chat_model
        """
        self.config = config or {}
        # Default chat model: prefer explicit config, then env, then fallback
        self.default_chat_model = (
            self.config.get("default_model")
            or self.config.get("default_chat_model")
            or os.environ.get("OLLAMA_CHAT_MODEL")
            or "llama2:7b"
        )
        # Default reasoning model: prefer explicit config, then env, then fallback
        self.default_reason_model = (
            self.config.get("default_reason_model")
            or os.environ.get("OLLAMA_REASON_MODEL")
            or "phi4-reasoning:14b"
        )

    def _run_ollama(self, model: str, prompt: str) -> dict:
        """
        Call Ollama using the Python library.
        """
        try:
            response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
            return {"text": response["message"]["content"]}
        except Exception as e:
            return {"text": f"(Ollama error: {e})"}

    def status(self) -> dict:
        """Return a small status dict used by the /ai/status endpoint."""
        return {
            "default_model": self.default_chat_model,
            "default_reason_model": self.default_reason_model,
        }

    def chat(self, prompt: str, model: str = None) -> dict:
        """
        General chat model call.
        """
        model_to_use = model or self.default_chat_model
        return self._run_ollama(model_to_use, prompt)

    def reason(self, prompt: str, model: str = None) -> dict:
        """
        Reasoning model call.
        """
        model_to_use = model or self.default_reason_model
        return self._run_ollama(model_to_use, prompt)

    def transcribe_audio(self, audio_bytes: bytes) -> str:
        return "(transcription not implemented)"

    def caption_image(self, img_bytes: bytes) -> str:
        return "(captioning not implemented)"
