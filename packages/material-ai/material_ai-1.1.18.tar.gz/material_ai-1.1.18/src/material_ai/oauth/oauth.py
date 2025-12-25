import threading
from .interface import IOAuthService
from .google_oauth import GoogleOAuthService

_lock = threading.Lock()
_oauth_instance: IOAuthService | None = None


def get_oauth() -> IOAuthService:
    global _oauth_instance
    with _lock:
        if _oauth_instance is None:
            _oauth_instance = GoogleOAuthService()
        return _oauth_instance
