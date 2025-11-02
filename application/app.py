from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify, send_file, send_from_directory
from .functions import cookie_handler, db_handler
from .functions.AI_handler import AIHandler 
import os
from dotenv import load_dotenv
import io
from piper.voice import PiperVoice

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Initialize DB on startup
db_handler.init_db()

# Initialize AI handler
ai_handler_instance = AIHandler()

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
        result = ai_handler_instance.handle_bot_request(request, user_id)
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)

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


@app.route('/img/<path:filename>')
def img_file(filename):
    return send_from_directory('img', filename)


@app.route('/tts', methods=['POST'])
def tts():
    text = request.form.get('text', '')
    # Clean the text
    import re
    text = re.sub(r'[^\w\s.,!?-]', '', text)  # Remove special chars except basic punctuation
    print(f"TTS text: '{text}'")
    if not text:
        return jsonify({"error": "No text provided"}), 400

    model_path = os.path.join(os.path.dirname(__file__), 'sound', 'en_GB-southern_english_female-low.onnx')
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


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True)
