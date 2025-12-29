import os
from cryptography.fernet import Fernet

class Config:
    def __init__(self):
        # Generate a random secret for cookie encryption at startup
        self.cookie_encryption_key = Fernet.generate_key()
        self.fernet = Fernet(self.cookie_encryption_key)
        self.totp_secret = os.environ.get("OPTDOOR_TOTP_SECRET", "BASE32SECRET3232")
        self.cookie_secret = os.environ.get("OPTDOOR_COOKIE_SECRET", "super-secret-key-change-me")
        self.cookie_name = os.environ.get("OPTDOOR_COOKIE_NAME", "OPTDOOR_AUTH")
        self.auth_path = os.environ.get("OPTDOOR_AUTH_PATH", "/_auth")
        self.check_path = os.environ.get("OPTDOOR_CHECK_PATH", "/_check")
        self.config_path = os.environ.get("OPTDOOR_CONFIG_PATH", "/_config")
        self.enable_config = False
        self.theme = os.environ.get("OPTDOOR_THEME", "dark")
        self.allowed_domains = os.environ.get("OPTDOOR_ALLOWED_DOMAINS", "").split(",")
        self.cookie_domain = os.environ.get("OPTDOOR_COOKIE_DOMAIN", None)
        self.cookie_secure = os.environ.get("OPTDOOR_COOKIE_SECURE", "true").lower() == "true"
        self.cookie_httponly = os.environ.get("OPTDOOR_COOKIE_HTTPONLY", "true").lower() == "true"
        self.cookie_samesite = os.environ.get("OPTDOOR_COOKIE_SAMESITE", "Lax")
        self.session_duration = int(os.environ.get("OPTDOOR_SESSION_DURATION", 86400)) # 1 day in seconds

config = Config()
