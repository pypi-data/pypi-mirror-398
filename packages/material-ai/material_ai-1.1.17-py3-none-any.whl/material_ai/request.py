from pydantic import BaseModel
from pydantic import Field


class FeedbackRequest(BaseModel):
    """Pydantic model for the feedback request body."""

    feedback_category: str
    feedback_text: str
    id: str
