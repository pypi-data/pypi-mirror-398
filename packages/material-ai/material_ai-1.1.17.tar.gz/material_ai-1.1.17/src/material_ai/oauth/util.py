import httpx
import logging
import functools
from json import JSONDecodeError
from .schema import OAuthErrorResponse


_logger = logging.getLogger(__name__)


def response_json_or_text(response: httpx.Response) -> dict | str:
    """
    Return parsed JSON or raw text from an httpx.Response.

    If the response content is valid JSON, it is parsed and returned as a dictionary.
    Otherwise, the raw response text is returned.

    Args:
        response: The httpx.Response instance to process.

    Returns:
        dict | str: Parsed JSON as a dictionary if the content is JSON,
        otherwise the raw text of the response.
    """
    try:
        details = response.json()
    except JSONDecodeError:
        details = response.text
    return details


def handle_httpx_errors(url: str = "Unknown API"):

    def decorator(func):
        """
        A decorator to catch common httpx errors and return a standardized
        OAuthErrorResponse.
        """

        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            _logger.debug(f"DEBUG: Requesting access token from {url}")
            try:
                return await func(self, *args, **kwargs)
            except httpx.RequestError as e:
                _logger.error(f"ERROR: Error requesting {url}: {e}", exc_info=e)
                return OAuthErrorResponse(
                    status_code=400, detail="Upstream OAuth Error"
                )
            except httpx.HTTPStatusError as e:
                _logger.warning(
                    f"ERROR: Non-200 error code returned from {url}: {e}, body: {e.response.text}"
                )
                return OAuthErrorResponse(
                    status_code=e.response.status_code,
                    detail=response_json_or_text(e.response),
                )
            except httpx.ConnectTimeout as e:
                _logger.warning(
                    f"ERROR: Non-200 error code returned from {url}: {e}, body: {e.response.text}"
                )
                return OAuthErrorResponse(
                    status_code=e.response.status_code,
                    detail=response_json_or_text(e.response),
                )
            except httpx.HTTPError as e:
                _logger.error(
                    f"ERROR: Unexpected HTTP error from {url}: {e}", exc_info=e
                )
                return OAuthErrorResponse(
                    status_code=500, detail="Internal Server Error"
                )
            except JSONDecodeError as e:
                _logger.error(
                    f"ERROR: Error decoding JSON response from {url}: {e}", exc_info=e
                )
                return OAuthErrorResponse(
                    status_code=401, detail="Response token JSON decode error"
                )
            except KeyError as e:
                _logger.error(
                    f"ERROR: Missing properties in response from {url}: {e}", exc_info=e
                )
                return OAuthErrorResponse(
                    status_code=401, detail="Response token missing access_token"
                )

        return wrapper

    return decorator
