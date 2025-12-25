__app_name__ = "material_ai"
__version__ = "1.1.17"

from .app import get_app
from .request import FeedbackRequest
from .oauth import (
    IOAuthService,
    OAuthRedirectionResponse,
    OAuthUserDetail,
    OAuthSuccessResponse,
)
from .oauth import OAuthErrorResponse, SSOConfig, handle_httpx_errors
