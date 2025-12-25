import pydantic
import threading
import logging
import pathlib
import yaml
from typing import List, Optional
from .theme import ThemeConfig


class ModelInfo(pydantic.BaseModel):
    model: str
    tagline: str


class Feedback(pydantic.BaseModel):
    value: str
    categories: Optional[List[str]]


class FeedbackInfo(pydantic.BaseModel):
    positive: Feedback
    negative: Feedback


class UIConfig(pydantic.BaseModel):
    """Defines the structured response for the config endpoint."""

    title: str
    greeting: str
    errorMessage: str
    models: List[ModelInfo]
    feedback: FeedbackInfo
    theme: ThemeConfig


DEFAULT_CONFIG = UIConfig(
    title="Gemini",
    greeting="What should we do today?",
    errorMessage="Some error has occured, Please try again later",
    models=[
        {"model": "2.5 Flash", "tagline": "Fast all-round help"},
        {"model": "2.5 Pro", "tagline": "Reasoning, math & code"},
    ],
    feedback={
        "positive": {"value": "GOOD", "categories": []},
        "negative": {
            "value": "BAD",
            "categories": [
                "Not / poorly personalized",
                "Problem with saving information",
                "Not factually correct",
                "Didn't follow instructions",
                "Offensive / Unsafe",
                "Wrong language",
            ],
        },
    },
    theme={
        "lightPalette": {
            "mode": "light",
            "primary": {
                "main": "#1a73e8",
            },
            "background": {
                "default": "#ffffff",
                "paper": "#f0f4f9",
                "card": "#f0f4f9",
                "cardHover": "#dde3ea",
                "history": "#d3e3fd",
            },
            "text": {
                "primary": "#07080aff",
                "secondary": "#1b1c1d",
                "tertiary": "#575b5f",
                "h5": "#1f1f1f",
                "selected": "#0842a0",
                "tagline": "#9a9b9c",
            },
            "tooltip": {
                "background": "#1b1c1d",
                "text": "#e8eaed",
            },
        },
        "darkPalette": {
            "mode": "dark",
            "primary": {
                "main": "#8ab4f8",
            },
            "background": {
                "default": "#1b1c1d",
                "paper": "#333537",
                "card": "#282a2c",
                "cardHover": "#3d3f42",
                "history": "#1f3760",
            },
            "text": {
                "primary": "#fff",
                "secondary": "#9aa0a6",
                "tertiary": "#a2a9b0",
                "h5": "#e3e3e3",
                "selected": "#d3e3fd",
                "tagline": "#747775",
            },
            "tooltip": {
                "background": "#fff",
                "text": "#1b1c1d",
            },
        },
    },
)
_config_instance: UIConfig | None = None
_lock = threading.Lock()
_logger = logging.getLogger(__name__)


def get_ui_config(ui_config_yaml) -> UIConfig:
    global _config_instance
    with _lock:
        if _config_instance is None:
            if ui_config_yaml is None:
                _config_instance = DEFAULT_CONFIG
                return _config_instance
            config_path = pathlib.Path(ui_config_yaml)
            if not config_path.exists() or not config_path.is_file():
                msg = f"WARNING: Config file not found at {config_path}"
                _logger.warning(msg)
                _config_instance = DEFAULT_CONFIG
                return _config_instance
            try:
                with open(config_path, "r") as file:
                    _config_instance = UIConfig(**yaml.safe_load(file))
            except Exception as e:
                msg = f"WARNING: Error loading ui configuration: {e}"
                _logger.warning(msg, exc_info=e)
                _config_instance = DEFAULT_CONFIG
    return _config_instance
