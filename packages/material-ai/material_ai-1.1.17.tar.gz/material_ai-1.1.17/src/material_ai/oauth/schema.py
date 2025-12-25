import pydantic
from typing import Any


class StatusCodeAndDetail(pydantic.BaseModel):
    """Represents a model for status codes and corresponding details.

    Used to encapsulate a status code and additional detail information.
    Primarily intended for scenarios where a status response with optional
    details needs to be represented.

    Attributes:
        status_code (int): The numerical status code typically following standard protocol or custom definitions.
        detail (str | dict[Any, Any]): The detailed information associated with the status code. Can be a string
            or a dictionary containing additional contextual data.
    """

    status_code: int
    detail: str | dict[Any, Any]


class SSOConfig(pydantic.BaseModel):
    """Captures all environment variables for sso."""

    client_id: str
    client_secret: str
    redirect_uri: str
    session_secret_key: str


class OAuthUserDetail(pydantic.BaseModel):
    """A typical user properties obtained from sso"""

    sub: str
    name: str
    given_name: str
    family_name: str
    picture: str
    email: str
    email_verified: bool


class OAuthSuccessResponse(pydantic.BaseModel):
    """A typical sso resposne to set cookies"""

    access_token: str
    refresh_token: str
    user_detail: OAuthUserDetail
    expires_in: int


class OAuthErrorResponse(StatusCodeAndDetail):
    """Response for a failed user login, including a status code and detail."""

    pass


class OAuthRedirectionResponse(pydantic.BaseModel):
    """A typical sso resposne to redirect user for sso login"""

    redirection_url: str
    state: str
