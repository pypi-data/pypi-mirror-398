import unittest
from unittest.mock import patch, MagicMock, call, AsyncMock
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
import material_ai.app as app_module
from material_ai.config import ConfigError
from material_ai.middleware import (
    AuthMiddleware,
    AddXAppHeaderMiddleware,
)


class TestGetAppFactory(unittest.TestCase):

    def setUp(self):
        """
        Reset the global singleton instance before each test to ensure isolation.
        """
        app_module._app_instance = None

    @patch("material_ai.app.get_config")
    @patch("material_ai.app.get_fast_api_app")
    @patch("material_ai.app._setup_app")
    def test_first_call_creates_app(
        self, mock_setup_app, mock_get_fast_api_app, mock_get_config
    ):
        """
        Verify that the first call to get_app correctly initializes the app.
        """
        # Arrange
        mock_app = MagicMock()
        mock_get_fast_api_app.return_value = mock_app

        # Act
        app_instance = app_module.get_app()

        # Assert
        mock_get_config.assert_called_once()
        mock_get_fast_api_app.assert_called_once()
        mock_setup_app.assert_called_once()
        self.assertIs(app_instance, mock_app)

    @patch("material_ai.app.get_config")
    @patch("material_ai.app.get_fast_api_app")
    @patch("material_ai.app._setup_app")
    def test_subsequent_calls_return_same_instance(
        self, mock_setup_app, mock_get_fast_api_app, mock_get_config
    ):
        """
        Verify that subsequent calls return the cached instance and do not re-run setup.
        """
        # Arrange
        mock_app = MagicMock()
        mock_get_fast_api_app.return_value = mock_app

        # Act
        first_instance = app_module.get_app()
        second_instance = app_module.get_app()

        # Assert: Check that setup functions were only called ONCE
        mock_get_config.assert_called_once()
        mock_get_fast_api_app.assert_called_once()
        mock_setup_app.assert_called_once()

        # Assert that both calls returned the exact same object
        self.assertIs(first_instance, second_instance)

    @patch("material_ai.app.StaticFiles")
    @patch("material_ai.api.router")
    @patch("material_ai.app.http_exception_handler")
    @patch("material_ai.app._setup_middleware")
    @patch("material_ai.app._setup_overrides")
    @patch("material_ai.app.get_oauth")
    @patch("material_ai.app._setup_logging")
    @patch("material_ai.app.get_config")
    def test_setup_app_happy_path(
        self,
        mock_get_config,
        mock_setup_logging,
        mock_get_oauth,
        mock_setup_overrides,
        mock_setup_middleware,
        mock_http_handler,
        mock_router,
        mock_static_files,
    ):
        """
        Verify that _setup_app calls all helper functions when oauth_service is None.
        """
        # Arrange: Create a mock FastAPI app and mock return values
        mock_app = MagicMock()
        mock_config = MagicMock()
        mock_oauth = MagicMock()
        mock_get_config.return_value = mock_config
        mock_get_oauth.return_value = mock_oauth

        # Act: Call the function under test
        app_module._setup_app(app=mock_app, oauth_service=None)

        # Assert: Check that all setup functions were called correctly
        mock_get_config.assert_called_once()
        mock_setup_logging.assert_called_once_with(mock_config)
        mock_get_oauth.assert_called_once()  # Should be called because service was None
        mock_setup_overrides.assert_called_once()
        mock_setup_middleware.assert_called_once_with(mock_app, mock_oauth)
        mock_app.add_exception_handler.assert_called_once_with(
            app_module.HTTPException, mock_http_handler
        )
        mock_app.include_router.assert_called_once_with(mock_router)
        mock_app.mount.assert_called_once_with(
            "/", mock_static_files.return_value, name="static"
        )

    @patch("material_ai.app._setup_middleware")
    @patch("material_ai.app.get_oauth")
    @patch("material_ai.app.get_config")
    def test_setup_app_with_provided_oauth_service(
        self, mock_get_config, mock_get_oauth, mock_setup_middleware
    ):
        """
        Verify that get_oauth is NOT called when an oauth_service is provided.
        """
        # Arrange
        mock_app = MagicMock()
        provided_oauth_service = MagicMock()

        # Act
        # We only need to patch the functions up to the point of interest
        with (
            patch("material_ai.app._setup_logging"),
            patch("material_ai.app._setup_overrides"),
            patch("material_ai.app.StaticFiles"),
            patch("material_ai.api.router"),
            patch("material_ai.app.http_exception_handler"),
        ):
            app_module._setup_app(app=mock_app, oauth_service=provided_oauth_service)

        # Assert
        mock_get_oauth.assert_not_called()
        mock_setup_middleware.assert_called_once_with(mock_app, provided_oauth_service)

    @patch("material_ai.app.get_config")
    def test_setup_app_raises_runtime_error_on_config_error(self, mock_get_config):
        """
        Verify that a RuntimeError is raised if get_config fails.
        """
        # Arrange
        mock_app = MagicMock()
        mock_get_config.side_effect = ConfigError("Bad config")

        # Act & Assert
        with self.assertRaises(RuntimeError):
            app_module._setup_app(app=mock_app)

    @patch("material_ai.app.get_config")
    @patch("material_ai.app._logger")
    def test_setup_middleware_in_production_mode(self, mock_logger, mock_get_config):
        """
        Verify that only the standard middleware is added when debug mode is OFF.
        """
        # Arrange: Configure mocks for a non-debug environment
        mock_app = MagicMock()
        mock_oauth_service = MagicMock()

        # Mock the config to return debug=False
        mock_config = MagicMock()
        mock_config.general.debug = False
        mock_config.sso.session_secret_key = "fake-secret"
        mock_get_config.return_value = mock_config

        # Act: Call the function under test
        app_module._setup_middleware(app=mock_app, oauth_service=mock_oauth_service)

        # Assert: Check that the correct middleware was added
        expected_calls = [
            call(SessionMiddleware, secret_key="fake-secret"),
            call(
                AddXAppHeaderMiddleware,
                app_name=app_module.__app_name__,
                app_version=app_module.__version__,
            ),
            call(AuthMiddleware, oauth_service=mock_oauth_service),
        ]
        mock_app.add_middleware.assert_has_calls(expected_calls, any_order=False)

        # Ensure CORSMiddleware was NOT added
        self.assertEqual(mock_app.add_middleware.call_count, 3)

    @patch("material_ai.app.get_config")
    @patch("material_ai.app._logger")
    def test_setup_middleware_in_debug_mode(self, mock_logger, mock_get_config):
        """
        Verify that CORSMiddleware is added when debug mode is ON.
        """
        # Arrange: Configure mocks for a debug environment
        mock_app = MagicMock()
        mock_oauth_service = MagicMock()

        # Mock the config to return debug=True
        mock_config = MagicMock()
        mock_config.general.debug = True
        mock_config.sso.session_secret_key = "fake-secret"
        mock_get_config.return_value = mock_config

        # Act: Call the function under test
        app_module._setup_middleware(app=mock_app, oauth_service=mock_oauth_service)

        # Assert: Check that the standard middleware AND CORS middleware were added
        expected_calls = [
            call(SessionMiddleware, secret_key="fake-secret"),
            call(
                CORSMiddleware,
                allow_origins=app_module.ALLOWED_ORIGINS,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            ),
            call(
                AddXAppHeaderMiddleware,
                app_name=app_module.__app_name__,
                app_version=app_module.__version__,
            ),
            call(AuthMiddleware, oauth_service=mock_oauth_service),
        ]
        mock_app.add_middleware.assert_has_calls(expected_calls, any_order=False)

        # Ensure exactly four middlewares were added
        self.assertEqual(mock_app.add_middleware.call_count, 4)

    @patch("material_ai.app.get_feedback_handler")
    @patch("material_ai.app.get_ui_configuration")
    @patch("material_ai.app.get_oauth_service")
    @patch("material_ai.app.get_ui_config")
    def test_overrides_with_feedback_handler(
        self, mock_get_ui_config, mock_get_oauth, mock_get_ui, mock_get_feedback
    ):
        """
        Verify that dependencies are overridden correctly when a feedback_handler is provided.
        """
        # Arrange
        mock_app = MagicMock()
        mock_app.dependency_overrides = {}  # Simulate the overrides dictionary
        mock_oauth_service = MagicMock()
        mock_ui_config_yaml = "path/to/config.yaml"
        mock_feedback_handler = MagicMock()
        mock_ui_config = MagicMock()
        mock_get_ui_config.return_value = mock_ui_config

        # Act
        app_module._setup_overrides(
            app=mock_app,
            oauth_service=mock_oauth_service,
            ui_config_yaml=mock_ui_config_yaml,
            feedback_handler=mock_feedback_handler,
        )

        # Assert
        # Check that the config was fetched
        mock_get_ui_config.assert_called_once_with(mock_ui_config_yaml)

        # Check that the overrides dictionary was populated correctly
        self.assertIn(mock_get_oauth, mock_app.dependency_overrides)
        self.assertIn(mock_get_ui, mock_app.dependency_overrides)
        self.assertIn(mock_get_feedback, mock_app.dependency_overrides)

        # Verify the content of the override functions
        self.assertEqual(
            mock_app.dependency_overrides[mock_get_oauth](), mock_oauth_service
        )
        self.assertEqual(mock_app.dependency_overrides[mock_get_ui](), mock_ui_config)
        self.assertEqual(
            mock_app.dependency_overrides[mock_get_feedback](), mock_feedback_handler
        )

    @patch("material_ai.app.Response")
    @patch("material_ai.app.get_feedback_handler", new_callable=AsyncMock)
    async def test_overrides_with_none_feedback_handler(
        self,
        mock_get_feedback,
        mock_response,
    ):
        """
        Verify the default no-op feedback handler is used when feedback_handler is None.
        """
        # Arrange
        mock_app = MagicMock()
        mock_app.dependency_overrides = {}
        mock_oauth_service = MagicMock()
        mock_ui_config_yaml = "path/to/config.yaml"

        # Act
        app_module._setup_overrides(
            app=mock_app,
            oauth_service=mock_oauth_service,
            ui_config_yaml=mock_ui_config_yaml,
            feedback_handler=None,  # Pass None for the handler
        )

        # Assert
        # Get the dynamically created override function for the feedback handler
        override_func = mock_app.dependency_overrides[mock_get_feedback]

        # Call the override function to execute the lambda
        lambda_handler = await override_func()

        lambda_handler(None)

        # Verify that the lambda called the Response class correctly
        mock_response.assert_called_once_with(status_code=200)

    @patch("material_ai.app.setup_structured_logging")
    @patch("material_ai.app.logging")
    def test_setup_logging_in_debug_mode(
        self, mock_logging, mock_setup_structured_logging
    ):
        """
        Verify logging is configured for DEBUG when config.general.debug is True.
        """
        # Arrange: Create a mock config object with debug mode enabled
        mock_config = MagicMock()
        mock_config.general.debug = True

        # Act: Call the function under test
        app_module._setup_logging(config=mock_config)

        # Assert: Check that setup_structured_logging was called with debug settings
        mock_setup_structured_logging.assert_called_once_with(
            app_name=app_module.__app_name__,
            enable_json_formatter=False,
            log_level=mock_logging.DEBUG,
        )

    @patch("material_ai.app.setup_structured_logging")
    @patch("material_ai.app.logging")
    def test_setup_logging_in_production_mode(
        self, mock_logging, mock_setup_structured_logging
    ):
        """
        Verify logging is configured for INFO and JSON when config.general.debug is False.
        """
        # Arrange: Create a mock config object with debug mode disabled
        mock_config = MagicMock()
        mock_config.general.debug = False

        # Act: Call the function under test
        app_module._setup_logging(config=mock_config)

        # Assert: Check that setup_structured_logging was called with production settings
        mock_setup_structured_logging.assert_called_once_with(
            app_name=app_module.__app_name__,
            enable_json_formatter=True,
            log_level=mock_logging.INFO,
        )
