from flask import Blueprint, render_template, request, redirect, url_for, session
from ..functions import cookie_handler

auth_bp = Blueprint('auth', __name__)

ADMIN_PASSWORD = '123'  # In production, use environment variable

@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin.admin_panel'))
        else:
            return render_template('admin_login.html', error='Invalid password')
    return render_template('admin_login.html')

@auth_bp.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('main.index'))

@auth_bp.route('/accept_cookies')
def accept_cookies():
    return cookie_handler.accept_cookies()

@auth_bp.route('/decline_cookies')
def decline_cookies():
    return cookie_handler.decline_cookies()

@auth_bp.route('/clear_cookies')
def clear_cookies():
    """Development helper: delete consent and user_id cookies and redirect to index."""
    resp = cookie_handler.clear_cookies()
    return resp