from fastapi import Response, HTTPException, Cookie
from fastapi.responses import RedirectResponse
from datetime import timedelta
from typing import Callable, Coroutine, Any, TypeAlias
import base64
import json
import logging
import hmac
import hashlib
from typing import Tuple, TypeAlias
from .exec import UnauthorizedException
from .config import get_config
from .request import FeedbackRequest
from .response import UserSuccessResponse
from .oauth import OAuthErrorResponse, OAuthSuccessResponse, OAuthUserDetail
from .oauth import IOAuthService

_logger = logging.getLogger(__name__)
FeedbackHandler: TypeAlias = Callable[[FeedbackRequest], Coroutine[Any, Any, Response]]


def verify_user_details(user_details: str) -> str | None:
    """
    Verifies the validity and integrity of a User Details.

    Parameters:
        user_deatils (str): The user details string to verify in the format "id.signature".

    Returns:
        str | None: The valid user details json if verification succeeds, otherwise None.
    """
    config = get_config()
    try:
        user_details, signature = user_details.split(".")
    except ValueError:
        return None

    user_details_bytes = user_details.encode("utf-8")

    calculated = hmac.new(
        config.sso.session_secret_key.encode("utf-8"),
        user_details_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated, signature):
        _logger.warning(
            f"WARNING: Invalid user id signature: {calculated} != {signature}"
        )
        return None

    _logger.debug(f"DEBUG: Verified user details: {user_details}")

    return base64.b64decode(user_details_bytes).decode("utf-8")


def _sign_user_details(user_details: OAuthUserDetail) -> str:
    """
    Signs and encodes user details for secure transfer by creating a Base64 encoded string
    and appending an HMAC SHA256 signature using a secret key. Ensures data integrity and
    validity during transmission.

    Args:
        user_details (UserDetails): The user details object to be signed and encoded.

    Returns:
        str: A single string containing the Base64 encoded user details followed by
        the HMAC signature, separated by a dot.
    """
    encoded_key = get_config().sso.session_secret_key.encode("utf-8")
    b64encoded_user_details = base64.b64encode(
        user_details.model_dump_json().encode("utf-8")
    )
    user_details_signature = hmac.new(
        encoded_key,
        b64encoded_user_details,
        hashlib.sha256,
    ).hexdigest()
    return f"{b64encoded_user_details.decode('utf-8')}.{user_details_signature}"


def _set_oauth_token_cookies(response: Response, oauth_response: OAuthSuccessResponse):
    """Sets authentication and user detail cookies on a FastAPI Response.

    This helper function sets three secure, HTTP-only cookies:
    1.  `access_token`: The short-lived token for API authentication.
    2.  `refresh_token`: The long-lived token used to get a new access token.
    3.  `user_details`: Signed user information to prevent client-side tampering.

    The 'secure' flag for cookies is enabled in production and disabled in
    debug mode to allow for HTTP testing.

    Args:
        response: The FastAPI Response object to be modified.
        oauth_response: An object containing the access token, refresh token,
                        and user details from the SSO provider.
    """
    config = get_config()
    response.set_cookie(
        key="access_token",
        value=oauth_response.access_token,
        httponly=True,
        secure=False if config.general.debug else True,
        max_age=oauth_response.expires_in,
        samesite="lax",
    )

    refresh_token_expiration = (
        oauth_response.expires_in + timedelta(days=2).total_seconds()
    )

    response.set_cookie(
        key="refresh_token",
        value=oauth_response.refresh_token,
        httponly=True,
        secure=False if config.general.debug else True,
        max_age=int(refresh_token_expiration),
        samesite="lax",
    )

    response.set_cookie(
        key="user_details",
        value=_sign_user_details(oauth_response.user_detail),
        httponly=True,
        secure=False if config.general.debug else True,
        max_age=oauth_response.expires_in,
        samesite="lax",
    )


def _remove_cookies(response: Response):
    """Deletes authentication-related cookies from a FastAPI Response.

    This is a helper function that removes the 'access_token', 'refresh_token',
    and 'user_details' cookies, effectively clearing the user's session
    from their browser.

    Args:
        response: The FastAPI Response object to be modified.
    """
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    response.delete_cookie("user_details")


async def remove_token(
    response: Response, refresh_token: str, oauth_service: IOAuthService
) -> Response:
    """Revokes a refresh token and clears authentication cookies.

    This function invalidates the user's session by revoking the provided
    refresh token with the SSO provider. Regardless of whether the server-side
    revocation is successful or if a token was provided, it proceeds to
    remove the authentication-related cookies from the user's browser.

    If no refresh token is provided, it simply clears the cookies.

    Args:
        response: The FastAPI Response object, which will be modified to
                  remove the cookies.
        refresh_token: The refresh token to be revoked. Can be None.

    Returns:
        The modified Response object with authentication cookies cleared.

    Raises:
        HTTPException: An exception with status code 500 if the SSO provider
                       fails to revoke the refresh token.
    """
    if refresh_token == None:
        _remove_cookies(response)
        return
    auth = oauth_service
    oauth_response = await auth.sso_revoke_refresh_token(refresh_token)
    if isinstance(oauth_response, OAuthErrorResponse):
        raise HTTPException(status_code=500)
    _remove_cookies(response)
    return response


def get_redirection_url(oauth_service: IOAuthService) -> Tuple[str, str]:
    """Generates the SSO redirection URL and a state parameter.

    This function creates the URL to which the user should be redirected to
    initiate the OAuth 2.0 authorization flow with the SSO provider. It also
    generates a unique 'state' value to be used for preventing Cross-Site
    Request Forgery (CSRF) attacks.

    Returns:
        A tuple containing two strings:
        - The state parameter (str).
        - The SSO redirection URL (str).
    """
    config = get_config()
    auth = oauth_service
    response = auth.sso_get_redirection_url(sso=config.sso)
    return (response.state, response.redirection_url)


async def get_user_details(
    response: Response, refresh_token: str, oauth_service: IOAuthService
) -> UserSuccessResponse:
    """Fetches user details by refreshing an OAuth access token.

    This function uses a provided refresh token to obtain a new access token
    from the SSO provider. If the token refresh is successful, it updates the
    OAuth tokens in the user's cookies and returns the user's details.

    This is typically used to re-validate a user's session or get updated
    user information when an access token has expired.

    Args:
        response: The FastAPI Response object, used to set the new
                  access and refresh token cookies.
        refresh_token: The OAuth refresh token used to obtain a new
                       access token.

    Returns:
        A UserSuccessResponse object containing the user's details.

    Raises:
        HTTPException: An exception with status code 500 if the
                       token refresh process fails.
    """

    config = get_config()
    auth = oauth_service
    oauth_response = await auth.sso_get_new_access_token(config.sso, refresh_token)

    if isinstance(oauth_response, OAuthErrorResponse):
        raise HTTPException(status_code=500)

    oauth_success_response: OAuthSuccessResponse = oauth_response

    _set_oauth_token_cookies(response, oauth_success_response)

    return UserSuccessResponse(user_response=oauth_success_response.user_detail)


async def on_callback(
    authorization_code: str, oauth_service: IOAuthService
) -> Response:
    """Handles the OAuth 2.0 callback after a user authorizes the application.

    This function is triggered when the user is redirected back from the SSO
    provider. It exchanges the provided authorization code for an access token
    and a refresh token.

    If the token exchange is successful, it sets the tokens as cookies in the
    user's browser and redirects them to the application's home page ("/").
    If the exchange fails, it raises an HTTP 500 error.

    Args:
        authorization_code: The authorization code provided by the SSO
                            provider as a query parameter.

    Returns:
        A RedirectResponse to the application's root URL with OAuth
        tokens set as cookies.

    Raises:
        HTTPException: If the token exchange with the SSO provider fails.
    """
    config = get_config()
    auth = oauth_service

    oauth_response = await auth.sso_get_access_token(config.sso, authorization_code)

    if isinstance(oauth_response, OAuthErrorResponse):
        raise HTTPException(status_code=500)

    response = RedirectResponse(url="/", status_code=302)

    _set_oauth_token_cookies(response, oauth_response)

    return response


def get_oauth_service() -> IOAuthService:
    raise NotImplementedError("This dependency must be overridden by the application.")


def get_ui_configuration() -> IOAuthService:
    raise NotImplementedError("This dependency must be overridden by the application.")


def get_feedback_handler() -> FeedbackHandler:
    raise NotImplementedError("This dependency must be overridden by the application.")


def get_user(
    user_details: str | None = Cookie(
        None, description="Cached user details as a JSON string."
    )
) -> OAuthUserDetail:
    verified_user_details = verify_user_details(user_details)
    if verified_user_details is None:
        raise UnauthorizedException()
    return OAuthUserDetail(**json.loads(verified_user_details))
