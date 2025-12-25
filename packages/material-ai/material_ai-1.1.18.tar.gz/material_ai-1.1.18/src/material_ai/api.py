import os
import logging
import psutil
from .app import get_endpoint_function, get_agent_loader
from google.adk.cli.adk_web_server import Session
from google.adk.agents import LlmAgent
from datetime import datetime, timezone
from fastapi import APIRouter, Response, Request, Cookie, status, Depends
from fastapi.responses import FileResponse, RedirectResponse
from .exec import UnauthorizedException
from .request import FeedbackRequest
from .app import STATIC_DIR
from . import __version__, __app_name__
import json
from .config import get_config
from .auth import (
    remove_token,
    get_redirection_url,
    get_user_details,
    on_callback,
    verify_user_details,
    get_oauth_service,
    get_ui_configuration,
    get_feedback_handler,
)
from .auth import IOAuthService, FeedbackHandler, get_user
from .oauth import OAuthUserDetail
from .response import UserSuccessResponse, HealthResponse, History, HistoryResponse
from .response import Agent, AgentResponse, List
from .ui_config import UIConfig

_logger = logging.getLogger(__name__)
router = APIRouter()
START_TIME = datetime.now(timezone.utc)


@router.get(
    "/",
    summary="Serve Frontend Application",
    description="Serves the main index.html file, which is the entry point for the web UI.",
    responses={
        200: {
            "description": "The main HTML page of the application.",
        }
    },
)
def root(request: Request):
    if "session_initialized" not in request.session:
        request.session["session_initialized"] = True
    return FileResponse(
        path=os.path.join(STATIC_DIR, "index.html"), media_type="text/html"
    )


@router.post(
    "/feedback",
    summary="Submit User Feedback",
    description="Receives and logs feedback sent from the user interface.",
    status_code=status.HTTP_200_OK,
)
async def feedback(
    feedback: FeedbackRequest,
    feedback_handler: FeedbackHandler = Depends(get_feedback_handler),
):
    _logger.info(f"INFO: SUCCESS: Feedback received from UI {feedback}")
    response = await feedback_handler(feedback)
    return response


@router.get(
    "/logout",
    summary="Log Out User and Invalidate Session",
    description="Revokes the user's refresh token with the provider and clears session cookies from the browser.",
    status_code=status.HTTP_200_OK,
    tags=["oauth"],
    responses={
        200: {
            "description": "Logout successful. Response includes headers to clear authentication cookies.",
        }
    },
)
async def logout(
    refresh_token: str | None = Cookie(None),
    oauth_service: IOAuthService = Depends(get_oauth_service),
):
    """
    Terminates the user's session.
    """
    # Here we logout the user and remove cookies
    response = Response(status_code=200)
    await remove_token(response, refresh_token, oauth_service)
    return response


@router.get(
    "/login",
    summary="Initiate OAuth 2.0 Login Flow",
    description="Redirects the user to the OAuth provider's authorization page and sets a CSRF token.",
    tags=["oauth"],
    responses={
        307: {
            "description": "Redirects to the OAuth provider. The 'Location' header contains the authorization URL."
        }
    },
)
async def login(
    request: Request, oauth_service: IOAuthService = Depends(get_oauth_service)
):
    """
    Redirects the user to OAuth 2.0 server for authentication.
    """
    # Generate a secure state token
    state, redirect_url = get_redirection_url(oauth_service)
    request.session["oauth_state"] = state
    _logger.debug(
        f"DEBUG: Redirecting to OAuth provider with oauth_state token with value: {state}"
    )
    return RedirectResponse(url=redirect_url)


@router.get(
    "/user",
    summary="Get Authenticated User's Details",
    description="Retrieves user info from a cache cookie or refreshes it using a refresh token cookie.",
    response_model=UserSuccessResponse,
    tags=["oauth"],
    responses={
        401: {"description": "Unauthorized. The refresh_token cookie is missing."},
    },
)
async def user(
    response: Response,
    user_details: str | None = Cookie(
        None, description="Cached user details as a JSON string."
    ),
    refresh_token: str | None = Cookie(
        None, description="Required refresh token for authentication."
    ),
    oauth_service: IOAuthService = Depends(get_oauth_service),
):
    """
    Handles user detail retrieval based on session cookies.
    """

    if user_details is not None:
        verified_user_details = verify_user_details(user_details)
        if verified_user_details is None:
            raise UnauthorizedException()
        return UserSuccessResponse(
            user_response=OAuthUserDetail(**json.loads(verified_user_details))
        )

    return await get_user_details(response, refresh_token, oauth_service)


@router.get(
    "/auth",
    summary="Handle OAuth 2.0 Provider Callback",
    description="Validates the state and exchanges the authorization code for an access token.",
    tags=["oauth"],
    responses={
        302: {
            "description": "Successful Authentication. The user is redirected to the frontend application with a session cookie."
        },
        403: {
            "description": "CSRF Detected. The 'state' parameter is invalid or missing."
        },
    },
)
async def callback(
    request: Request,
    code: str,
    state: str,
    oauth_service: IOAuthService = Depends(get_oauth_service),
):
    """
    Handles the callback from OAuth2.0 after user authentication.
    """
    stored_state = request.session.get("oauth_state")
    if not stored_state or stored_state != state:
        _logger.error(
            f"ERROR: Session missmatch stored state: {stored_state}, not same as state: {state}"
        )
        return Response(status_code=403)
    return await on_callback(code, oauth_service)


@router.get(
    "/health",
    summary="Get service health and system information",
    response_model=HealthResponse,
    tags=["Monitoring"],
)
async def health_check():
    """
    Provides a detailed health status of the service, including uptime and
    current system resource utilization (CPU, Memory, Disk).
    """
    config = get_config()
    # 1. Calculate Uptime
    uptime_delta = datetime.now(timezone.utc) - START_TIME

    # 2. Get System Metrics using psutil
    memory_info = psutil.virtual_memory()
    disk_info = psutil.disk_usage("/")

    system_data = {
        "cpu_percent_used": psutil.cpu_percent(),
        "memory": {
            "total": f"{memory_info.total / (1024**3):.2f} GB",
            "available": f"{memory_info.available / (1024**3):.2f} GB",
            "percent_used": memory_info.percent,
        },
        "disk": {
            "total": f"{disk_info.total / (1024**3):.2f} GB",
            "used": f"{disk_info.used / (1024**3):.2f} GB",
            "free": f"{disk_info.free / (1024**3):.2f} GB",
            "percent_used": disk_info.percent,
        },
    }

    return HealthResponse(
        status="ok",
        uptime=str(uptime_delta),
        system=system_data,
        debug=config.general.debug,
        appName=__app_name__,
        version=__version__,
    )


@router.get(
    "/config",
    summary="Get ui config information",
    response_model=UIConfig,
    tags=["Configuration"],
)
async def config(ui_configuration: UIConfig = Depends(get_ui_configuration)):
    return ui_configuration


@router.get(
    "/apps/{app_name}/history",
    summary="Get session history",
    response_model=HistoryResponse,
)
async def history(app_name: str, user: OAuthUserDetail = Depends(get_user)):
    list_sessions = get_endpoint_function("list_sessions")
    get_session = get_endpoint_function("get_session")

    def get_title(session_instance: Session) -> str:
        try:
            text_content = session_instance.events[0].content.parts[0].text
            return text_content
        except (IndexError, AttributeError):
            return "..."

    sessions: list[Session] = await list_sessions(app_name, user.sub)
    sessions.sort(key=lambda s: s.last_update_time, reverse=True)
    history = []
    for session in sessions:
        session_instance: Session = await get_session(app_name, user.sub, session.id)
        history.append(
            History(
                id=session.id,
                title=get_title(session_instance),
                last_update_time=session.last_update_time * 1000,
                app_name=session.app_name,
            )
        )

    return HistoryResponse(history=history)


@router.get(
    "/agents",
    summary="Get list of active agents",
)
async def agents():
    agent_loader = get_agent_loader()
    if not agent_loader:
        return []
    agents: List[Agent] = []

    def format_agent_name(name):
        """
        Converts snake_case (greeting_agent) to Title Case (Greeting Agent).
        """
        if not name:
            return ""
        return name.replace("_", " ").title()

    for agent in agent_loader.list_agents():
        base_agent = agent_loader.load_agent(agent)
        model = ""
        if isinstance(base_agent, LlmAgent):
            model = base_agent.model
        agents.append(
            Agent(
                id=agent,
                model=model,
                name=format_agent_name(agent),
                description=base_agent.description,
                status="active",
            )
        )

    return AgentResponse(agents=agents)
