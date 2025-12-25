import threading
import logging
import os
from typing import Optional, Mapping, Any
from fastapi import FastAPI, HTTPException, Response
from fastapi.routing import APIRoute
from google.adk.cli.fast_api import get_fast_api_app, AgentLoader
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .middleware import AddXAppHeaderMiddleware, AuthMiddleware
from .handler import http_exception_handler
from .config import get_config, Config
from .exec import ConfigError
from .oauth import get_oauth
from .log_config import setup_structured_logging
from .auth import (
    get_oauth_service,
    get_ui_configuration,
    get_feedback_handler,
)
from .auth import FeedbackHandler
from .oauth import IOAuthService
from .ui_config import get_ui_config
from . import __app_name__, __version__

_lock = threading.Lock()
_logger = logging.getLogger(__name__)
_app_instance: FastAPI | None = None
_agent_loader: AgentLoader | None = None
_lock = threading.Lock()

STATIC_DIR = f"{os.path.dirname(os.path.abspath(__file__))}/ui/dist"
UI_CONFIG_YAML = f"{os.path.dirname(os.path.abspath(__file__))}/ui/ui_config.yaml"
AGENT_DIR = f"{os.path.dirname(os.path.abspath(__file__))}/agents"
ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:5173",
    "http://127.0.0.1",
    "http://127.0.0.1:5173",
]


def _setup_logging(config: Config):
    """Initializes and configures structured logging for the application.

    This function sets up the application's logging system based on the
    provided configuration. It enables or disables JSON-formatted logs and sets
    the appropriate log level depending on whether the application is in
    debug mode.

    In debug mode, logging is set to the DEBUG level with plain text format.
    In production (non-debug) mode, logging is set to the INFO level with
    JSON format for easier parsing by log aggregation systems.

    Args:
        config (Config): The application's configuration object, which contains
            the debug flag.
    """
    json_logs_enabled = False if config.general.debug else True
    setup_structured_logging(
        app_name=__app_name__,
        enable_json_formatter=json_logs_enabled,
        log_level=logging.DEBUG if config.general.debug else logging.INFO,
    )


async def default_feedback_handler(_):
    return Response(status_code=200)


def _setup_overrides(
    app: FastAPI,
    oauth_service: IOAuthService,
    ui_config_yaml: str,
    feedback_handler: FeedbackHandler,
):
    """Sets up dependency overrides for the FastAPI application.

    This function is used to inject specific instances of services and
    configurations into the FastAPI dependency injection system. It is
    particularly useful for testing or running the application in specific
    modes where standard dependencies need to be replaced with mocks or
    alternative implementations.

    It overrides the dependencies for the OAuth service, the UI configuration,
    and the feedback handler.

    Args:
        app (FastAPI): The FastAPI application instance whose dependencies
            will be overridden.
        oauth_service (IOAuthService): The specific OAuth service instance
            to inject into the application.
        ui_config_yaml (str): The path to the YAML file containing the UI
            configuration.
        feedback_handler (FeedbackHandler): The handler for processing
            feedback. If set to None, a default no-op handler that returns a
            200 status code is used instead.
    """
    ui_config = get_ui_config(ui_config_yaml)

    def override_get_oauth_service() -> IOAuthService:
        return oauth_service

    def override_get_ui_configuration() -> IOAuthService:
        return ui_config

    def override_get_feedback_handler() -> FeedbackHandler:
        if feedback_handler == None:
            return default_feedback_handler
        return feedback_handler

    app.dependency_overrides[get_oauth_service] = override_get_oauth_service
    app.dependency_overrides[get_ui_configuration] = override_get_ui_configuration
    app.dependency_overrides[get_feedback_handler] = override_get_feedback_handler


def _setup_middleware(app: FastAPI, oauth_service: IOAuthService):
    """Configures and adds all necessary middleware to the FastAPI application.

    This function adds standard middleware for authentication (AuthMiddleware),
    custom application headers (AddXAppHeaderMiddleware), and session management
    (SessionMiddleware).

    If the application is running in debug mode (determined by the global
    config), it will also add CORSMiddleware to allow for cross-origin
    requests from specified origins.

    Args:
        app (FastAPI): The FastAPI application instance to which the
            middleware will be added.
        oauth_service (IOAuthService): The authentication service instance
            required by the AuthMiddleware.
    """
    config = get_config()
    app.add_middleware(SessionMiddleware, secret_key=config.sso.session_secret_key)
    if config.general.debug:
        _logger.debug("DEBUG: App running in DEBUG mode")

        # Apply cors middleware in debug mode
        app.add_middleware(
            CORSMiddleware,
            allow_origins=ALLOWED_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.add_middleware(
        AddXAppHeaderMiddleware,
        app_name=__app_name__,
        app_version=__version__,
    )
    app.add_middleware(AuthMiddleware, oauth_service=oauth_service)


def _setup_app(
    app: FastAPI,
    oauth_service: IOAuthService = None,
    ui_config_yaml: str = None,
    feedback_handler: FeedbackHandler = None,
) -> None:
    """
    Configures the FastAPI application with middleware, logging,
    based on the provided configuration settings. This setup is intended for use in environments
    such as GKE or similar platforms that support structured log parsing. Debug mode adjustments
    and security considerations are also applied. API routes are registered during setup.

    Args:
        app (FastAPI): The FastAPI application instance to configure.
        oauth_service (IOAuthService, optional): An instance of the OAuth
            service for authentication. Defaults to GoogleOAuthService.
        ui_config_yaml (str): The file path to the UI configuration YAML.
        feedback_handler: A handler function to handle user feedback

    Raises:
        RuntimeError: If the configuration is invalid or cannot be loaded.
    """
    # If we can't configure the app, exit immediately
    try:
        config = get_config()
    except ConfigError as e:
        raise RuntimeError("Bad configuration") from e  # lol :P

    _setup_logging(config)

    if oauth_service == None:
        oauth_service = get_oauth()

    _setup_overrides(app, oauth_service, ui_config_yaml, feedback_handler)

    _setup_middleware(app, oauth_service)

    app.add_exception_handler(HTTPException, http_exception_handler)
    from .api import router as core_router

    app.include_router(core_router)
    app.mount("/", StaticFiles(directory=STATIC_DIR), name="static")


def get_app(
    agent_dir: str = AGENT_DIR,
    oauth_service: IOAuthService = None,
    ui_config_yaml: str = UI_CONFIG_YAML,
    feedback_handler: FeedbackHandler = None,
    adk_kwargs: Optional[Mapping[str, Any]] = {},
):
    """Factory function to get the singleton FastAPI application instance.

    This function ensures that only one instance of the FastAPI application is
    created during the application's lifecycle. It uses a thread-safe lock to
    manage instantiation, guaranteeing a single, shared app object. This
    approach also prevents circular import issues by providing a centralized
    access point.

    Args:
        agent_dir (str): The directory path for the agent.
        oauth_service (IOAuthService, optional): An instance of the OAuth
            service for authentication. Defaults to GoogleOAuthService.
        ui_config_yaml (str): The file path to the UI configuration YAML.
        feedback_handler: A handler function to handle user feedback. caller can implement
            their own feedback logic.

    Returns:
        FastAPI: The singleton instance of the FastAPI application.
    """
    global _app_instance
    global _agent_loader
    with _lock:
        if _app_instance is None:
            config = get_config()
            app = get_fast_api_app(
                agents_dir=agent_dir,
                web=False,
                allow_origins=ALLOWED_ORIGINS if config.general.debug else [],
                session_service_uri=config.adk.session_db_url,
                **adk_kwargs,
            )
            _setup_app(app, oauth_service, ui_config_yaml, feedback_handler)
            _app_instance = app
            _agent_loader = AgentLoader(agent_dir)

        return _app_instance


def get_app_instance() -> FastAPI | None:
    return _app_instance


def get_endpoint_function(function_name: str):
    """
    Searches app.routes for a route where the endpoint function name matches.
    """
    instance = get_app_instance()
    if not instance:
        return None
    for route in get_app_instance().routes:
        if isinstance(route, APIRoute):
            if route.name == function_name:
                return route.endpoint
    return None


def get_agent_loader() -> AgentLoader | None:
    return _agent_loader
