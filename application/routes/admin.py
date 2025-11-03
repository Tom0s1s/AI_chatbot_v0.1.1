from flask import Blueprint, render_template, request, jsonify, make_response, send_file
from ..functions import db_handler
import io
import csv

admin_bp = Blueprint('admin', __name__)

# Admin authentication decorator
def admin_required(f):
    def wrapper(*args, **kwargs):
        from flask import session, redirect, url_for
        if not session.get('admin_logged_in'):
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@admin_bp.route('/admin')
@admin_required
def admin_panel():
    # Allow optional ?user_id=... to view other users (admin use)
    user_id = request.args.get('user_id') or request.cookies.get("user_id")
    if not user_id:
        return "No user_id provided or cookie set."

    # Get the full chat history (no limit)
    events = db_handler.get_events(user_id, limit=500)  # adjust limit as needed

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

@admin_bp.route('/admin/users')
@admin_required
def admin_users():
    # return JSON list of users
    users = db_handler.list_users()
    return jsonify([{"id": u[0], "info": u[1]} for u in users])

@admin_bp.route('/admin/export')
@admin_required
def admin_export():
    # export events as CSV for a given user_id (query param or cookie)
    user_id = request.args.get('user_id') or request.cookies.get('user_id')
    if not user_id:
        return "No user_id provided", 400

    events = db_handler.get_events(user_id, limit=10000)
    # events: list of (event_type, content, timestamp)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['event_type', 'content', 'timestamp'])
    for et, content, ts in events[::-1]:  # oldest first
        writer.writerow([et, content, ts])

    resp = make_response(output.getvalue())
    resp.headers['Content-Type'] = 'text/csv'
    resp.headers['Content-Disposition'] = f'attachment; filename=events_{user_id}.csv'
    return resp

@admin_bp.route('/admin/clear', methods=['POST'])
@admin_required
def admin_clear():
    # clear events for provided user_id (form or JSON) or cookie
    user_id = request.form.get('user_id') or (request.get_json() or {}).get('user_id') or request.cookies.get('user_id')
    if not user_id:
        return jsonify({'ok': False, 'error': 'no user_id provided'}), 400
    db_handler.clear_events(user_id)
    return jsonify({'ok': True})