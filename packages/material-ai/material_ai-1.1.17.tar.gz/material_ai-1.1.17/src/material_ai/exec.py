from fastapi import HTTPException, status

""" This module contains custom exceptions. """


class ConfigError(Exception):
    """We throw this for invaid configuration file."""

    pass


class UnauthorizedException(HTTPException):
    """We throw this any unauthorized request."""

    def __init__(
        self, detail: str = "Not authenticated or session expired", headers: dict = None
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers=headers or {"WWW-Authenticate": "Bearer"},
        )
