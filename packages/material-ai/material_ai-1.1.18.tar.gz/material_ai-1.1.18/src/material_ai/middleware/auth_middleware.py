import json
import logging
import http.cookies
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from material_ai.exec import UnauthorizedException
from material_ai.oauth import (
    OAuthUserDetail,
    IOAuthService,
    OAuthErrorResponse,
    oauth_user_details_context,
)
from material_ai.exec import UnauthorizedException
from material_ai.auth import verify_user_details, _remove_cookies


_logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Adds the X-App header, with app name and version, to all responses."""

    def __init__(self, app, oauth_service: IOAuthService):
        super().__init__(app)
        self.oauth_service = oauth_service

    async def dispatch(self, request, call_next):
        route = request.url.path
        EXCLUDED_PATHS = [
            "/",
            "/login",
            "/health",
            "/config",
            "/auth",
            "/icon.svg",
            "/favicon.ico",
            "/.well-known/appspecific/com.chrome.devtools.json",
            "/gemini.svg",
        ]
        EXCLUDED_PREFIXES = ["/assets/"]
        is_excluded_path = route in EXCLUDED_PATHS or any(
            route.startswith(prefix) for prefix in EXCLUDED_PREFIXES
        )

        if is_excluded_path:
            return await call_next(request)

        cookies_header = request.headers.get("cookie")

        try:
            if not cookies_header:
                raise UnauthorizedException()

            cookies = http.cookies.SimpleCookie()
            cookies.load(cookies_header)

            if cookies.get("refresh_token") == None:
                raise UnauthorizedException()

            if route == "/user":
                return await call_next(request)

            if cookies.get("access_token") == None:
                raise UnauthorizedException()
            if cookies.get("user_details") == None:
                raise UnauthorizedException()

            auth = self.oauth_service

            access_token_cookie = cookies.get("access_token")

            oauth_response = await auth.sso_verify_access_token(
                access_token_cookie.value
            )

            if not oauth_response:
                raise UnauthorizedException()

            if isinstance(oauth_response, OAuthErrorResponse):
                raise UnauthorizedException()

            uid = str(oauth_response)

            # If we want to cross check if given user can call this API
            # We dont want other actors to modify user session
            if "users" in route:
                user_id = _extract_user_id_from_path(route)
                if user_id and user_id != uid:
                    raise UnauthorizedException()

            if not route in ["/run_sse", "/run"]:
                return await call_next(request)

            user_details_cookie = cookies.get("user_details")
            decoded_user_details = verify_user_details(user_details_cookie.value)
            if decoded_user_details == None:
                raise UnauthorizedException()

            user_details = OAuthUserDetail(**json.loads(decoded_user_details))

            oauth_user_details_context.set(user_details)
            body_bytes = await request.body()

            async def receive():
                return {"type": "http.request", "body": body_bytes}

            json_payload = json.loads(body_bytes.decode("utf-8"))
            if "user_id" in json_payload and json_payload["user_id"] != uid:
                raise UnauthorizedException()
            new_request = Request(request.scope, receive)
            return await call_next(new_request)

        except UnauthorizedException as e:
            response = Response(status_code=401, content="Unauthorized")
            _remove_cookies(response)
            return response
        except Exception as e:
            _logger.error(
                f"ERROR: Error decoding JSON response from {route}: {e}", exc_info=e
            )
            response = Response(status_code=500, content="Internal Server Error")
            return response


def _extract_user_id_from_path(path: str) -> str | None:
    """
    If the segment '/users/' exists in a URL path, this function extracts
    the very next segment, which is assumed to be the user ID.

    Args:
        path: The URL path string (e.g., "/apps/my-app/users/12312321/sessions").

    Returns:
        The user ID as a string if found, otherwise None.
    """
    try:
        parts = path.strip("/").split("/")

        users_index = parts.index("users")

        if users_index + 1 < len(parts):
            return parts[users_index + 1]

        return None

    except ValueError:
        return None
