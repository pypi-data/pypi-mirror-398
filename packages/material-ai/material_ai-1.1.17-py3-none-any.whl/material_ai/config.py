import configparser
import os
import threading
import logging
import pydantic
import pathlib
from .exec import ConfigError
from typing import Any
from dotenv import load_dotenv
from .oauth import SSOConfig

load_dotenv()


class GeneralConfig(pydantic.BaseModel):
    debug: bool


class ADKConfig(pydantic.BaseModel):
    session_db_url: str


class GoogleConfig(pydantic.BaseModel):
    genai_use_vertexai: str
    api_key: str


class Config(pydantic.BaseModel):
    sso: SSOConfig
    general: GeneralConfig
    adk: ADKConfig
    google: GoogleConfig


_logger = logging.getLogger(__name__)
_lock = threading.Lock()
_config_instance: Config | None = None


def get_config() -> Config:
    """
    Retrieves the global configuration instance, ensuring it is only loaded once from a
    specified path defined in the CONFIG_PATH environment variable. If the configuration
    file is invalid, non-existent, or the environment variable is not set, it raises an error.

    Returns:
        Config: The global configuration object.

    Raises:
        ConfigError: If the configuration file cannot be located, read, or parsed properly.
    """
    global _config_instance
    with _lock:
        if _config_instance is None:
            config_path_from_env = os.environ.get("CONFIG_PATH")
            if not config_path_from_env:
                msg = "ERROR: Environment variable CONFIG_PATH not set"
                _logger.error(msg)
                raise ConfigError(msg)

            config_path = pathlib.Path(config_path_from_env)
            if not config_path.exists() or not config_path.is_file():
                msg = f"ERROR: Config file not found at {config_path}"
                _logger.error(msg)
                raise ConfigError(msg)

            try:
                _config_instance = _configure(config_path)
            except Exception as e:
                msg = f"ERROR: Error loading configuration: {e}"
                _logger.error(msg, exc_info=e)
                raise ConfigError(msg) from e
    return _config_instance


def _configure(path: pathlib.Path) -> Config:
    """Load configuration from config.ini and populate pydantic models.
    Environment variables take precedence over config file values.
    Environment variable naming convention: SECTION_PARAMETER
    Example: SSO_REDIRECT_URI for [SSO] section's REDIRECT_URI parameter

    Arguments:
        path: Path to config file as a pathlib.Path object

    Returns:
        Config: The loaded configuration.
    """
    config_parser = configparser.ConfigParser()
    if not path.is_file():
        raise FileNotFoundError(
            f"config file {path} is not a valid file or does not exist."
        )
    config_parser.read(path)
    sso = SSOConfig(
        client_id=get_config_value(config_parser, "SSO", "client_id"),
        client_secret=get_config_value(config_parser, "SSO", "client_secret"),
        redirect_uri=get_config_value(config_parser, "SSO", "redirect_uri"),
        session_secret_key=get_config_value(config_parser, "SSO", "session_secret_key"),
    )
    general = GeneralConfig(
        debug=get_config_value(config_parser, "GENERAL", "debug"),
    )
    adk = ADKConfig(
        session_db_url=get_config_value(config_parser, "ADK", "session_db_url"),
    )
    google = GoogleConfig(
        genai_use_vertexai=get_config_value(
            config_parser, "GOOGLE", "genai_use_vertexai"
        ),
        api_key=get_config_value(config_parser, "GOOGLE", "api_key"),
    )
    return Config(sso=sso, general=general, adk=adk, google=google)


# We use this sentinel object to detect if a default value was provided
_sentinel = object()


def get_config_value(
    config_parser: configparser.ConfigParser,
    section: str,
    parameter: str,
    default: Any = _sentinel,
) -> Any:
    """Get config value from the environment variable or config file.

    If a default value is not provided, the configuration is considered
    required. If the value is not found in environment variables or the
    config file, a ConfigError is raised.

    Args:
        config_parser: Instance of a config parser to look up
        section: Config section name
        parameter: Parameter name in the section
        default: Default value if not provided, value is required.

    Returns:
        The configuration value from the environment or config file.

    Raises:
        ConfigError: If the configuration is required and not found.
    """
    env_var_name = f"{section}_{parameter}".upper()
    env_value = os.environ.get(env_var_name)

    # Always use env var first
    if env_value is not None:
        _logger.debug(f"DEBUG: Using environment variable {env_var_name}")
        return env_value

    if default is _sentinel:
        try:
            return config_parser.get(section, parameter)
        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            raise ConfigError(
                f"Required configuration not found: [{section}] {parameter}"
            ) from e
    else:
        # Fallback to the config file
        return config_parser.get(section, parameter, fallback=default)
