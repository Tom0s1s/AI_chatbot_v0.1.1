from flask import Blueprint, request, jsonify, send_file, send_from_directory
from ..functions.AI_handler import AIHandler
import os
import io
import re

api_bp = Blueprint('api', __name__)

# Initialize AI handler
ai_handler_instance = AIHandler()

@api_bp.route('/current_user')
def current_user():
    """Return current user info as JSON."""
    from ..functions import db_handler
    user_id = request.cookies.get('user_id')
    if not user_id:
        return jsonify({}), 200
    user_info = db_handler.get_user(user_id)
    short_id = user_id[:5] if len(user_id) > 5 else user_id
    return jsonify({"user": {"id": user_id, "short": short_id, "info": user_info or ""}})

@api_bp.route('/ai/status')
def ai_status():
    """Return a JSON status of available AI drivers."""
    try:
        model = os.environ.get("OLLAMA_CHAT_MODEL", "llama2:13b")
        status = {"default_model": model}
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify({"ok": True, "status": status})

@api_bp.route('/img/<path:filename>')
def img_file(filename):
    return send_from_directory('img', filename)

@api_bp.route('/tts', methods=['POST'])
def tts():
    text = request.form.get('text', '')
    # Clean the text
    text = re.sub(r'[^\w\s.,!?-]', '', text)  # Remove special chars except basic punctuation
    print(f"TTS text: '{text}'")
    if not text:
        return jsonify({"error": "No text provided"}), 400

    model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sound', 'en_GB-southern_english_female-low.onnx')
    if not os.path.exists(model_path):
        return jsonify({"error": "TTS model not found"}), 500

    try:
        from piper.voice import PiperVoice
        voice = PiperVoice.load(model_path)
        wav_data = io.BytesIO()
        voice.synthesize(text, wav_data)
        wav_data.seek(0)
        return send_file(wav_data, mimetype='audio/wav', download_name='tts.wav')
    except Exception as e:
        return jsonify({"error": f"TTS error: {str(e)}"}), 500