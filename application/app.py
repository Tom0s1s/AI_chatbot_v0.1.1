from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify
from .functions import cookie_handler, db_handler
from .functions.AI_handler import AIHandler
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# Build AI handler config from environment so the runtime can be switched without
# changing code. Useful variables:
#  - OLLAMA_CHAT_MODEL: default model name
#  - USE_OLLAMA_CLI: if '0' or 'false' will prefer HTTP
#  - OLLAMA_HTTP_URL: URL to post {model, prompt} to as a fallback
ai_config = {
    "default_model": os.environ.get("OLLAMA_CHAT_MODEL"),
    "use_ollama_cli": os.environ.get("USE_OLLAMA_CLI", "1").lower() not in ("0", "false", "no"),
    "ollama_http_url": os.environ.get("OLLAMA_HTTP_URL"),
    # If you want to force the app to only use the Ollama CLI (no HTTP fallback),
    # set FORCE_OLLAMA_CLI=1 in the environment or change this value to True.
    "force_cli_only": os.environ.get("FORCE_OLLAMA_CLI", "0").lower() in ("1", "true", "yes"),
}

ai_handler = AIHandler(config=ai_config)

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
            audio_bytes = audio_file.read()
            try:
                transcription = ai_handler.transcribe_audio(audio_bytes)
                user_message = transcription
            except Exception as e:
                # If transcription fails, return informative error
                return jsonify({"error": "Audio transcription failed", "detail": str(e)}), 500

        # 2) image file (multipart form file 'image')
        image_file = request.files.get('image')
        image_caption = None
        if image_file:
            img_bytes = image_file.read()
            try:
                image_caption = ai_handler.caption_image(img_bytes)
            except Exception as e:
                # If captioning fails, include a warning but continue
                image_caption = None

        # 3) textual message field
        if not user_message:
            user_message = request.form.get("message")

        if not user_message and not image_caption:
            return jsonify({"error": "No input provided"}), 400

        # Log the original user input (if available)
        logged_input = user_message or f"[image only] caption:{image_caption}"
        db_handler.add_event(user_id, "chat_user", logged_input)

        # Build memory prompt (last 20 events only)
        memory_prompt = db_handler.build_memory_prompt(user_id, limit=20)

        # Build an LLM prompt by combining memory and the new user message and optional image caption.
        prompt_parts = [memory_prompt]
        if user_message:
            prompt_parts.append("User: " + user_message)
        if image_caption:
            prompt_parts.append("[Image description]: " + image_caption)
        prompt = "\n\n".join([p for p in prompt_parts if p]).strip()

        # Allow caller to request 'reason' mode (uses reasoning model) via form flag 'mode=reason'
        mode = request.form.get('mode') or (request.args.get('mode') if request.method == 'GET' else None)
        model = request.form.get('model') or None

        # Ask configured AI handler for a reply. Fall back to an echo on error.
        try:
            if mode == 'reason':
                llm_result = ai_handler.reason(prompt, model=model) if model else ai_handler.reason(prompt)
            else:
                llm_result = ai_handler.chat(prompt, model=model) if model else ai_handler.chat(prompt)

            assistant_reply = llm_result.get("text") if isinstance(llm_result, dict) else str(llm_result)
        except Exception as e:
            # Log and fall back
            import logging
            logging.exception("LLM chat failed: %s", e)
            assistant_reply = f"(Fallback) You said: {user_message or '[image]'}"

        # Log assistant reply
        db_handler.add_event(user_id, "chat_llm", assistant_reply)

        return jsonify({
            "reply": assistant_reply,
            "memory_prompt": memory_prompt
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


@app.route('/ai/status')
def ai_status():
    """Return a JSON status of available AI drivers."""
    try:
        status = ai_handler.status()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify({"ok": True, "status": status})


@app.route('/current_user')
def current_user():
    """Return a small JSON object describing the current user (based on cookie).
    Used by the frontend to display who is currently using the chat.
    """
    user_id = request.cookies.get('user_id')
    if not user_id:
        return jsonify({"user": None})

    # Pull any stored info from the DB (may be empty string)
    try:
        info = db_handler.get_user(user_id) or ""
    except Exception:
        info = ""

    # Provide a short display id so we don't have to render a long UUID everywhere
    short = user_id.split('-')[0] if isinstance(user_id, str) else None
    return jsonify({"user": {"id": user_id, "short": short, "info": info}})

if __name__ == '__main__':
    app.run(debug=True)
