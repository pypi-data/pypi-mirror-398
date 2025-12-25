from fastapi import Request, HTTPException, Response
from material_ai.auth import _remove_cookies


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Catches any HTTPException. If the status code is 401 (Unauthorized),
    it clears authentication cookies before returning the error response.
    """
    # If the exception is a 401 Unauthorized, clear the cookies
    if exc.status_code == 401:
        # Create a standard JSON response for the 401 error
        response = Response(status_code=401, content="Unauthorized")
        _remove_cookies(response)
        return response

    # For all other HTTPExceptions, fall back to the default behavior
    return Response(
        status_code=exc.status_code,
    )
