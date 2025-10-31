#Creates and handles cookies * UUID -> user info mapping -> send to DB (pandas?)
import os
import uuid
from flask import request, make_response, redirect, url_for
from . import db_handler

# Default cookie settings (sane production defaults). We'll allow runtime
# adjustments for local development (localhost/127.0.0.1) so cookies can be
# set without HTTPS during development.
COOKIE_SETTINGS = {
    "httponly": True,
    "samesite": "Lax",
    "secure": True,
    "path": "/",
}


def _effective_cookie_settings(override: dict | None = None) -> dict:
    cfg = COOKIE_SETTINGS.copy()
    # If running on localhost or 127.0.0.1 disable the 'secure' flag so the
    # cookie can be set over plain HTTP during local development.
    try:
        host = request.host or ""
        if host.startswith("127.0.0.1") or host.startswith("localhost"):
            cfg["secure"] = False
    except RuntimeError:
        # request may not be available outside a request context; keep defaults
        pass
    if override:
        cfg.update(override)
    return cfg


def set_cookie(response, key, value, days_expire=365, httponly: bool | None = None):
    max_age = days_expire * 24 * 60 * 60
    override = {}
    if httponly is not None:
        override["httponly"] = httponly
    cfg = _effective_cookie_settings(override)
    response.set_cookie(key, value, max_age=max_age, **cfg)
    return response

def get_cookie(key):
    return request.cookies.get(key)

def delete_cookie(response, key):
    response.delete_cookie(key, path="/")
    return response

def has_cookie_consent():
    return str(request.cookies.get("consent") or "").lower() in ("true", "1")

def accept_cookies():
    """Set consent=true and assign a unique user_id if missing."""
    # consent cookie is useful to read from client-side JS; don't set httponly
    # for the consent flag so the banner can be hidden immediately.
    resp = make_response(redirect(url_for("index")))
    resp = set_cookie(resp, "consent", "true", httponly=False)

    if not get_cookie("user_id"):
        user_id = str(uuid.uuid4())
        # Keep the user_id httponly for privacy
        resp = set_cookie(resp, "user_id", user_id, httponly=True)

        # Insert into DB with placeholder info
        db_handler.add_user(user_id, user_info="")

    return resp

def decline_cookies():
    """Set consent=false and redirect."""
    # keep consent readable by JS so banner remains hidden appropriately
    resp = make_response(redirect(url_for("index")))
    return set_cookie(resp, "consent", "false", httponly=False)



