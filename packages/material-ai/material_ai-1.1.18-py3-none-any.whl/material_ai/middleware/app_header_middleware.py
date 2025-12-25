import time
from starlette.middleware.base import BaseHTTPMiddleware


class AddXAppHeaderMiddleware(BaseHTTPMiddleware):
    """Adds the X-App header, with app name and version, to all responses."""

    def __init__(self, app, app_name: str, app_version: str):
        super().__init__(app)
        self.app_name = app_name
        self.app_version = app_version

    async def dispatch(self, request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-AppInfo"] = f"{self.app_name}/{self.app_version}"
        return response
