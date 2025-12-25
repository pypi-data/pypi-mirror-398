from contextvars import ContextVar
from . import OAuthUserDetail


oauth_user_details_context: ContextVar[OAuthUserDetail | None] = ContextVar(
    "oauth_user_details_context", default=None
)
