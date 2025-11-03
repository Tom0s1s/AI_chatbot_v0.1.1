from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from ..functions.AI_handler import AIHandler
from ..functions import db_handler

main_bp = Blueprint('main', __name__)

# Initialize AI handler
ai_handler_instance = AIHandler()

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/bot', methods=['GET', 'POST'])
def bot():
    if request.method == 'POST':
        user_id = request.cookies.get("user_id")
        if not user_id:
            return redirect(url_for('main.index'))
        result = ai_handler_instance.handle_bot_request(request, user_id)
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)

    return render_template('bot.html')

@main_bp.route('/info')
def info():
    """Render the info page (template may be empty for now)."""
    return render_template('info.html')