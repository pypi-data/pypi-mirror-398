import pyotp
import html
import os
from flask import Flask, request, make_response, redirect, render_template, url_for
from urllib.parse import urlparse
from datetime import datetime, timedelta, timezone
from .config import config

app = Flask(__name__)
# Flask's secret key is for sessions/signing, but we use config.fernet for the auth cookie
app.secret_key = config.cookie_secret

def is_safe_origin(origin):
    if not origin:
        return False
    if origin.startswith("/"):
        return True
    
    try:
        u = urlparse(origin)
        if not u.hostname:
            return False
        
        if not config.allowed_domains or config.allowed_domains == ['']:
            return False

        return any(u.hostname.endswith(domain.strip()) for domain in config.allowed_domains if domain.strip())
    except Exception:
        return False

def get_totp():
    return pyotp.TOTP(config.totp_secret)

def encrypt_session(expires_at: datetime) -> str:
    payload = expires_at.isoformat().encode()
    return config.fernet.encrypt(payload).decode()

def decrypt_session(token: str) -> datetime:
    try:
        payload = config.fernet.decrypt(token.encode())
        return datetime.fromisoformat(payload.decode())
    except Exception:
        return None

@app.route(config.check_path, methods=['GET'])
def check():
    token = request.cookies.get(config.cookie_name)
    if token:
        expires_at = decrypt_session(token)
        if expires_at and expires_at > datetime.now(timezone.utc):
            return "OK", 200
    
    return "Unauthorized", 401

@app.route(config.auth_path, methods=['GET'])
def auth_get():
    origin = request.args.get("originator", "/")
    if not is_safe_origin(origin):
        origin = "/"
    
    return render_template("login.html", origin=origin, auth_path=config.auth_path, theme=config.theme)

@app.route(config.auth_path, methods=['POST'])
def auth_post():
    code = request.form.get("code")
    origin = request.form.get("originator", "/")
    if not is_safe_origin(origin):
        origin = "/"

    totp = get_totp()
    if totp.verify(code):
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=config.session_duration)
        token = encrypt_session(expires_at)
        
        resp = make_response(redirect(origin))
        resp.set_cookie(
            config.cookie_name,
            token,
            max_age=config.session_duration,
            httponly=config.cookie_httponly,
            secure=config.cookie_secure,
            samesite=config.cookie_samesite,
            domain=config.cookie_domain
        )
        return resp
    
    return render_template("login.html", origin=origin, auth_path=config.auth_path, error="Invalid code", theme=config.theme), 403

@app.route(config.config_path, methods=['GET'])
def config_get():
    if not config.enable_config:
        return "Not Found", 404
    issuer = os.environ.get("OPTDOOR_ISSUER", "OTPdoor")
    user = os.environ.get("OPTDOOR_USER", "admin")
    provisioning_uri = pyotp.totp.TOTP(config.totp_secret).provisioning_uri(name=user, issuer_name=issuer)
    
    # Calculate display duration and unit
    display_duration = config.session_duration
    unit = "seconds"
    if display_duration % 3600 == 0:
        display_duration //= 3600
        unit = "hours"
    elif display_duration % 60 == 0:
        display_duration //= 60
        unit = "minutes"

    return render_template("config.html", 
                           secret=config.totp_secret, 
                           display_duration=display_duration,
                           unit=unit,
                           theme=config.theme,
                           provisioning_uri=provisioning_uri,
                           auth_path=config.auth_path)

@app.route(config.config_path, methods=['POST'])
def config_post():
    if not config.enable_config:
        return "Not Found", 404
    action = request.form.get("action")
    message = ""
    if action == "new_secret":
        config.totp_secret = pyotp.random_base32()
        message = "New TOTP secret generated!"
    elif action == "update_duration":
        try:
            val = int(request.form.get("duration", 86400))
            unit = request.form.get("unit", "seconds")
            if unit == "minutes":
                val *= 60
            elif unit == "hours":
                val *= 3600
            config.session_duration = val
            message = f"Session duration updated to {config.session_duration} seconds."
        except ValueError:
            message = "Error: Invalid duration value."
    elif action == "update_theme":
        config.theme = request.form.get("theme", "dark")
        message = f"Theme updated to {config.theme} mode."

    issuer = os.environ.get("OPTDOOR_ISSUER", "OTPdoor")
    user = os.environ.get("OPTDOOR_USER", "admin")
    provisioning_uri = pyotp.totp.TOTP(config.totp_secret).provisioning_uri(name=user, issuer_name=issuer)

    # Calculate display duration and unit for the refresh
    display_duration = config.session_duration
    unit = "seconds"
    if display_duration % 3600 == 0:
        display_duration //= 3600
        unit = "hours"
    elif display_duration % 60 == 0:
        display_duration //= 60
        unit = "minutes"

    return render_template("config.html", 
                           secret=config.totp_secret, 
                           display_duration=display_duration,
                           unit=unit,
                           theme=config.theme,
                           provisioning_uri=provisioning_uri,
                           auth_path=config.auth_path,
                           message=message)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
