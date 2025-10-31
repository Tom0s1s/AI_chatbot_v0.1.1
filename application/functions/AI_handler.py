import subprocess
import json
import os
import shutil
from typing import Optional, Dict, Any
import requests

class AIHandler:
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Lightweight AI handler.

        Accepts an optional config dict with keys like:
          - default_model / default_chat_model
          - use_ollama_cli (bool)
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
        # Detect whether ollama CLI is available
        self.ollama_cli_path = shutil.which("ollama")
        # allow explicit config to disable CLI even if present
        self.use_ollama_cli = bool(self.config.get("use_ollama_cli", True)) and bool(self.ollama_cli_path)

        # Optional Ollama HTTP endpoint fallback (set OLLAMA_HTTP_URL env var or config)
        self.ollama_http_url = self.config.get("ollama_http_url") or os.environ.get("OLLAMA_HTTP_URL")
        self.use_ollama_http = bool(self.ollama_http_url)
        # Force CLI-only mode if requested (no HTTP fallback)
        env_force = str(os.environ.get("FORCE_OLLAMA_CLI") or "").lower()
        cfg_force = self.config.get("force_cli_only")
        if cfg_force is None:
            # if not explicitly set in config, honor env var
            self.force_cli_only = env_force in ("1", "true", "yes")
        else:
            self.force_cli_only = bool(cfg_force)

    def _run_ollama(self, model: str, prompt: str) -> dict:
        """
        Call Ollama HTTP API at localhost:11434/api/generate
        """
        try:
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            res = requests.post(url, json=payload, timeout=60)
            res.raise_for_status()
            data = res.json()
            return {"text": data.get("response", "").strip()}
        except Exception as e:
            return {"text": f"(Ollama API error: {e})"}

    def _run_ollama_http(self, model: str, prompt: str) -> dict:
        """Post to a simple Ollama HTTP-style endpoint. The server URL is
        provided in `self.ollama_http_url` and should accept JSON like
        {"model": "<model>", "prompt": "<prompt>"} and return JSON with a
        key containing the model text (common keys: 'response', 'text', 'output').
        This is a tolerant parser to support different local wrappers.
        """
        if not self.ollama_http_url:
            return {"text": "(no HTTP endpoint configured)"}

        try:
            payload = {"model": model, "prompt": prompt}
            res = requests.post(self.ollama_http_url, json=payload, timeout=30)
            res.raise_for_status()
            j = res.json()

            # tolerant parsing of likely response shapes
            if isinstance(j, dict):
                # common keys
                for k in ("response", "text", "output", "result"):
                    if k in j and isinstance(j[k], str) and j[k].strip():
                        return {"text": j[k].strip()}

                # sometimes output is nested
                if "results" in j and isinstance(j["results"], list) and j["results"]:
                    last = j["results"][-1]
                    if isinstance(last, dict):
                        for k in ("content", "text", "response"):
                            if k in last and isinstance(last[k], str):
                                return {"text": last[k].strip()}

            # fallback: return the raw JSON string
            return {"text": json.dumps(j)[:200]}
        except Exception as e:
            return {"text": f"(HTTP request failed: {e})"}

    def status(self) -> dict:
        """Return a small status dict used by the /ai/status endpoint."""
        return {
            "default_model": self.default_chat_model,
            "default_reason_model": self.default_reason_model,
            "ollama_cli": bool(self.ollama_cli_path),
            "ollama_cli_path": self.ollama_cli_path,
            "use_ollama_cli": self.use_ollama_cli,
            "ollama_http_url": self.ollama_http_url,
            "use_ollama_http": self.use_ollama_http,
            "force_cli_only": getattr(self, "force_cli_only", False),
        }

    def chat(self, prompt: str, model: str = None) -> dict:
        """
        General chat model call.
        """
        model_to_use = model or self.default_chat_model
        # If configured to force CLI-only, require the CLI and do not fall back
        if getattr(self, "force_cli_only", False):
            if not self.use_ollama_cli:
                return {"text": "(LLM error: Ollama CLI required but not available)"}
            return self._run_ollama(model_to_use, prompt)

        # Prefer CLI if available and enabled, otherwise fall back to HTTP endpoint.
        if self.use_ollama_cli:
            return self._run_ollama(model_to_use, prompt)
        if self.use_ollama_http:
            return self._run_ollama_http(model_to_use, prompt)
        return {"text": "(no LLM backend configured — install ollama or set OLLAMA_HTTP_URL)"}

    def reason(self, prompt: str, model: str = None) -> dict:
        """
        Reasoning model call.
        """
        model_to_use = model or self.default_reason_model
        # If configured to force CLI-only, require the CLI and do not fall back
        if getattr(self, "force_cli_only", False):
            if not self.use_ollama_cli:
                return {"text": "(LLM error: Ollama CLI required but not available)"}
            return self._run_ollama(model_to_use, prompt)

        # Prefer CLI if available and enabled, otherwise fall back to HTTP endpoint.
        if self.use_ollama_cli:
            return self._run_ollama(model_to_use, prompt)
        if self.use_ollama_http:
            return self._run_ollama_http(model_to_use, prompt)
        return {"text": "(no LLM backend configured — install ollama or set OLLAMA_HTTP_URL)"}

    def transcribe_audio(self, audio_bytes: bytes) -> str:
        return "(transcription not implemented)"

    def caption_image(self, img_bytes: bytes) -> str:
        return "(captioning not implemented)"
