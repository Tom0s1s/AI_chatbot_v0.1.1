from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify, send_file
from .functions import cookie_handler, db_handler
import os
from dotenv import load_dotenv
import ollama
import io
from piper.voice import PiperVoice
import whisper
import warnings

# Suppress Whisper FP16 warning
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Initialize DB on startup
db_handler.init_db()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/accept_cookies')
def accept_cookies():
    return cookie_handler.accept_cookies()


@app.route('/decline_cookies')
def decline_cookies():
    return cookie_handler.decline_cookies()


@app.route('/clear_cookies')
def clear_cookies():
    """Development helper: delete consent and user_id cookies and redirect to index."""
    resp = make_response(redirect(url_for("index")))
    # Use cookie_handler helper to delete cookies so behavior is consistent
    resp = cookie_handler.delete_cookie(resp, "consent")
    resp = cookie_handler.delete_cookie(resp, "user_id")
    return resp

@app.route('/bot', methods=['GET', 'POST'])
def bot():
    if request.method == 'POST':
        user_id = request.cookies.get("user_id")
        if not user_id:
            return redirect(url_for("index"))
        # Determine input: prefer uploaded audio, then image, then text form
        user_message = None
        # 1) audio file (multipart form file 'audio')
        audio_file = request.files.get('audio')
        if audio_file:
            # Save the wav file temporarily
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                audio_file.save(temp_file)
                audio_path = temp_file.name
            print(f"Audio file saved to {audio_path}")
            # Transcribe using Whisper
            try:
                model = whisper.load_model("tiny")
                result = model.transcribe(audio_path)
                user_message = result["text"].strip()
                print(f"Transcription: '{user_message}'")
            except Exception as e:
                print(f"Transcription failed: {e}")
                user_message = "Sorry, I couldn't understand the audio. Please try again or type your message."
            finally:
                # Clean up temp file
                if os.path.exists(audio_path):
                    os.unlink(audio_path)

        # 2) image file (multipart form file 'image')
        image_file = request.files.get('image')
        image_caption = None
        if image_file:
            # img_bytes = image_file.read()
            # image_caption = ai_handler.caption_image(img_bytes)
            image_caption = "(Image captioning not implemented yet)"

        # 3) textual message field
        if not user_message:
            user_message = request.form.get("message")

        if not user_message and not image_caption:
            return jsonify({"error": "No input provided"}), 400

        # Log the original user input (if available)
        logged_input = user_message or f"[image only] caption:{image_caption}"
        db_handler.add_event(user_id, "chat_user", logged_input)

        # Build memory messages (last 20 events only)
        events = db_handler.get_events(user_id, limit=20)
        # Reverse so oldest is first
        events = events[::-1]
        
        # Construct messages for LLM
        messages = [{"role": "system", "content": "You are a helpful AI assistant. Respond naturally without mentioning your model or introducing yourself unless asked."}]
        for event_type, content, timestamp in events:
            if event_type == "chat_user":
                messages.append({"role": "user", "content": content})
            elif event_type == "chat_llm":
                messages.append({"role": "assistant", "content": content})
            # Ignore other event types for now

        # Add the current user message
        if user_message:
            messages.append({"role": "user", "content": user_message})
        if image_caption:
            messages.append({"role": "user", "content": f"[Image description]: {image_caption}"})

        model = request.form.get('model') or os.environ.get("OLLAMA_CHAT_MODEL", "llama2:13b")

        # Ask the LLM for a reply. Fall back to an echo on error.
        try:
            response = ollama.chat(model=model, messages=messages)
            assistant_reply = response["message"]["content"]
        except Exception as e:
            # Log and fall back
            import logging
            logging.exception("LLM chat failed: %s", e)
            assistant_reply = f"(Fallback) You said: {user_message or '[image]'}"

        # Log assistant reply
        db_handler.add_event(user_id, "chat_llm", assistant_reply)

        return jsonify({
            "reply": assistant_reply
        })

    return render_template('bot.html')

@app.route('/admin')
def admin():
    # Allow optional ?user_id=... to view other users (admin use)
    user_id = request.args.get('user_id') or request.cookies.get("user_id")
    if not user_id:
        return "No user_id provided or cookie set."

    # Get the full chat history (no limit)
    events = db_handler.get_events(user_id, limit=500)  # adjust limit as needed

    # Format into a readable transcript
    transcript = []
    for event_type, content, timestamp in events[::-1]:  # reverse so oldest first
        if event_type == "chat_user":
            transcript.append(f"<b>User:</b> {content} <small>({timestamp})</small>")
        elif event_type == "chat_llm":
            transcript.append(f"<b>Assistant:</b> {content} <small>({timestamp})</small>")
        elif event_type == "annotation":
            transcript.append(f"<i>[Annotation]</i> {content} <small>({timestamp})</small>")
        else:
            transcript.append(f"[{event_type}] {content} <small>({timestamp})</small>")

    return render_template('admin.html', transcript=transcript)


@app.route('/admin/users')
def admin_users():
    # return JSON list of users
    users = db_handler.list_users()
    return jsonify([{"id": u[0], "info": u[1]} for u in users])


@app.route('/admin/export')
def admin_export():
    # export events as CSV for a given user_id (query param or cookie)
    user_id = request.args.get('user_id') or request.cookies.get('user_id')
    if not user_id:
        return "No user_id provided", 400

    events = db_handler.get_events(user_id, limit=10000)
    # events: list of (event_type, content, timestamp)
    import io, csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['event_type', 'content', 'timestamp'])
    for et, content, ts in events[::-1]:  # oldest first
        writer.writerow([et, content, ts])

    resp = make_response(output.getvalue())
    resp.headers['Content-Type'] = 'text/csv'
    resp.headers['Content-Disposition'] = f'attachment; filename=events_{user_id}.csv'
    return resp


@app.route('/admin/clear', methods=['POST'])
def admin_clear():
    # clear events for provided user_id (form or JSON) or cookie
    user_id = request.form.get('user_id') or (request.get_json() or {}).get('user_id') or request.cookies.get('user_id')
    if not user_id:
        return jsonify({'ok': False, 'error': 'no user_id provided'}), 400
    db_handler.clear_events(user_id)
    return jsonify({'ok': True})


@app.route('/info')
def info():
    """Render the info page (template may be empty for now)."""
    return render_template('info.html')


@app.route('/current_user')
def current_user():
    """Return current user info as JSON."""
    user_id = request.cookies.get('user_id')
    if not user_id:
        return jsonify({}), 200
    user_info = db_handler.get_user(user_id)
    short_id = user_id[:5] if len(user_id) > 5 else user_id
    return jsonify({"user": {"id": user_id, "short": short_id, "info": user_info or ""}})


@app.route('/ai/status')
def ai_status():
    """Return a JSON status of available AI drivers."""
    try:
        model = os.environ.get("OLLAMA_CHAT_MODEL", "llama2:13b")
        status = {"default_model": model}
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify({"ok": True, "status": status})


@app.route('/tts', methods=['POST'])
def tts():
    text = request.form.get('text', '')
    if not text:
        return jsonify({"error": "No text provided"}), 400

    model_path = os.path.join(os.getcwd(), 'application', 'sound', 'en_GB-southern_english_female-low.onnx')
    if not os.path.exists(model_path):
        return jsonify({"error": "TTS model not found"}), 500

    try:
        voice = PiperVoice.load(model_path)
        wav_data = io.BytesIO()
        voice.synthesize(text, wav_data)
        wav_data.seek(0)
        return send_file(wav_data, mimetype='audio/wav', as_attachment=True, download_name='tts.wav')
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True)
