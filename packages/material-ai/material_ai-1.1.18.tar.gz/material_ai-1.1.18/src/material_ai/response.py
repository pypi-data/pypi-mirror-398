import pydantic
from pydantic import Field
from typing import Any, List
from .oauth import OAuthUserDetail


class UserSuccessResponse(pydantic.BaseModel):
    """Response for a successful user login.

    Attributes:
        user_response: Contains details about the logged-in user.
    """

    user_response: OAuthUserDetail


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


# --- Pydantic Models for a Structured Response ---


class MemoryHealth(pydantic.BaseModel):
    total: str
    available: str
    percent_used: float


class DiskHealth(pydantic.BaseModel):
    total: str
    used: str
    free: str
    percent_used: float


class SystemHealth(pydantic.BaseModel):
    cpu_percent_used: float = Field(
        ..., description="Current system-wide CPU utilization as a percentage."
    )
    memory: MemoryHealth
    disk: DiskHealth


class HealthResponse(pydantic.BaseModel):
    """Defines the structured response for the health check endpoint."""

    status: str = Field(
        "ok", description="Indicates the operational status of the service."
    )
    uptime: str = Field(..., description="Service uptime duration in HH:MM:SS format.")
    system: SystemHealth
    debug: bool
    appName: str
    version: str


class History(pydantic.BaseModel):
    id: str
    title: str
    last_update_time: float
    app_name: str


class HistoryResponse(pydantic.BaseModel):
    history: List[History]


class Agent(pydantic.BaseModel):
    id: str
    name: str
    description: str
    model: str
    status: str


class AgentResponse(pydantic.BaseModel):
    agents: List[Agent]
