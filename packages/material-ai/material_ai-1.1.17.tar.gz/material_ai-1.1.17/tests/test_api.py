# tests/test_api.py

import unittest
import os
import json
from unittest.mock import patch, MagicMock, AsyncMock, ANY, PropertyMock
from fastapi import status
from material_ai import FeedbackRequest
from fastapi.testclient import TestClient
from starlette.responses import RedirectResponse
from material_ai.app import STATIC_DIR, get_app
from material_ai.api import (
    get_oauth_service,
    get_ui_configuration,
    get_feedback_handler,
    UserSuccessResponse,
    OAuthUserDetail,
)
from material_ai.ui_config import UIConfig
from material_ai.config import Config, SSOConfig, ADKConfig, GeneralConfig, GoogleConfig
import material_ai.app as app_module
from material_ai.oauth import OAuthErrorResponse


@patch("material_ai.app.get_config")
class TestAPIEndpoints(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        """
        Set up a clean app, client, and mock StaticFiles for each test.
        """
        app_module._app_instance = None

        self.config_patch = patch("material_ai.app.get_config")
        mock_get_config = self.config_patch.start()

        # Configure the mock to return a valid config with a string secret_key
        mock_config = create_dummy_config(False)
        mock_get_config.return_value = mock_config
        # 1. Start a patch to replace the real StaticFiles class with a mock
        self.static_files_patch = patch("material_ai.app.StaticFiles")
        self.mock_static_files = self.static_files_patch.start()

        self.file_response_patch = patch("material_ai.api.FileResponse")
        self.mock_file_response = self.file_response_patch.start()
        self.maxDiff = None
        self.mock_oauth_service = AsyncMock()

        self.mock_oauth_service.sso_verify_access_token.return_value = "test_user_123"

        # 2. Set up the rest of the app and client
        app = get_app(oauth_service=self.mock_oauth_service)

        self.cookies = {
            "refresh_token": "test_refresh_token",
            "access_token": "test_access_token",
            "user_details": "test_user_details",
        }

        self.mock_ui_config = create_dummy_ui_config()
        self.mock_feedback_handler = AsyncMock()
        app.dependency_overrides[get_oauth_service] = lambda: self.mock_oauth_service
        app.dependency_overrides[get_ui_configuration] = lambda: self.mock_ui_config
        app.dependency_overrides[get_feedback_handler] = (
            lambda: self.mock_feedback_handler
        )

        self.client = TestClient(app, cookies=self.cookies)

    def tearDown(self):
        """
        Clean up dependency overrides and stop patches after each test.
        """
        get_app().dependency_overrides.clear()
        # Stop the patch to restore the original StaticFiles class
        self.static_files_patch.stop()
        self.config_patch.stop()
        self.file_response_patch.stop()

    @patch("material_ai.api.on_callback", new_callable=AsyncMock)
    @patch("fastapi.Request.session", new_callable=PropertyMock)
    async def test_callback_fails_with_mismatched_state(
        self, mock_session_property, mock_on_callback, mock_get_config
    ):
        """
        Tests that the /auth callback returns 403 Forbidden if the state does not match.
        """
        # --- Arrange ---
        # 1. The state stored in the session is different from the one in the query.
        mock_session_object = MagicMock()
        mock_session_object.get.return_value = "state-in-session"
        mock_session_property.return_value = mock_session_object
        query_state = "different-state-in-query"

        # --- Act ---
        response = self.client.get(f"/auth?code=anycode&state={query_state}")

        # --- Assert ---
        # 2. Check for a 403 Forbidden status code.
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Crucially, ensure the on_callback helper was never called.
        mock_on_callback.assert_not_awaited()

    @patch("material_ai.api.on_callback", new_callable=AsyncMock)
    @patch("fastapi.Request.session", new_callable=PropertyMock)
    async def test_callback_fails_with_no_stored_state(
        self, mock_session_property, mock_on_callback, mock_get_config
    ):
        """
        Tests that the /auth callback returns 403 Forbidden if no state is in the session.
        """
        # --- Arrange ---
        mock_session_object = MagicMock()
        mock_session_object.get.return_value = None

        mock_session_property.return_value = mock_session_object

        # --- Act ---
        response = self.client.get("/auth?code=anycode&state=anystate")

        # --- Assert ---
        # 2. Check for a 403 Forbidden status code.
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Ensure the on_callback helper was never called.
        mock_on_callback.assert_not_awaited()

    @patch("material_ai.api.on_callback", new_callable=AsyncMock)
    @patch("fastapi.Request.session", new_callable=PropertyMock)
    async def test_callback_success_with_valid_state(
        self, mock_session_property, mock_on_callback, mock_get_config
    ):
        """
        Tests the /auth callback with a valid state.
        """
        # --- Arrange ---
        test_state = "secret-csrf-token-123"
        auth_code = "authorization-code-456"

        mock_session_object = MagicMock()

        mock_session_object.get.return_value = test_state

        mock_session_property.return_value = mock_session_object

        # Configure the other mock as before
        expected_response = RedirectResponse(url="/", status_code=302)
        mock_on_callback.return_value = expected_response

        # --- Act ---
        self.client.get(f"/auth?code={auth_code}&state={test_state}")

        # --- Assert ---
        # Now the comparison 'stored_state != state' will work correctly
        # because stored_state will be "secret-csrf-token-123"
        mock_session_object.get.assert_called_once_with("oauth_state")
        mock_on_callback.assert_awaited_once_with(auth_code, self.mock_oauth_service)

    def test_user_unauthorized_when_no_refresh_token(self, mock_get_config):
        """
        Tests that /user returns 401 Unauthorized if the refresh_token cookie is missing.
        """

        self.client.cookies = {"refresh_token": None}
        response = self.client.get("/user")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("material_ai.api.verify_user_details")
    def test_user_returns_details_from_cache_cookie(
        self, mock_verify_user_details, mock_get_config
    ):
        """
        Tests that /user successfully returns user details from the 'user_details' cookie
        when it is present and valid.
        """
        # --- Arrange ---
        # 1. Create dummy user data
        user_data = {
            "sub": "12345",
            "name": "Test User",
            "email": "test@example.com",
            "given_name": "Test User",
            "family_name": "Test User",
            "picture": "Test pitcure",
            "email_verified": True,
        }
        user_details_json = json.dumps(user_data)

        # 2. Configure the mock helper to return the valid JSON string
        mock_verify_user_details.return_value = user_details_json

        # --- Act ---
        response = self.client.get("/user")

        # --- Assert ---
        # 4. Check for a successful response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 5. Verify the helper was called correctly
        mock_verify_user_details.assert_called_once_with("test_user_details")

        # 6. Check that the response body matches the expected structure and data
        expected_response = {"user_response": user_data}
        self.assertEqual(response.json(), expected_response)

    @patch("material_ai.api.get_user_details", new_callable=AsyncMock)
    async def test_user_fetches_details_when_cache_is_missing(
        self, mock_get_user_details, mock_get_config
    ):
        """
        Tests that /user calls the get_user_details helper when the cache cookie is missing.
        """
        test_token = "a-valid-refresh-token"
        expected_response_obj = UserSuccessResponse(
            user_response=OAuthUserDetail(
                sub="12345",
                name="Fresh User",
                given_name="Fresh User",
                family_name="Fresh User",
                picture="Test pitcure",
                email="test@test.com",
                email_verified=True,
            )
        )

        mock_get_user_details.return_value = expected_response_obj
        self.client.cookies = {"refresh_token": "test_refresh_token"}
        response = self.client.get("/user")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.json(), json.loads(expected_response_obj.model_dump_json())
        )

    @patch("material_ai.api.get_redirection_url")
    def test_login_redirects_and_sets_state(
        self, mock_get_redirection_url, mock_get_config
    ):
        """
        Tests that the /login endpoint correctly sets the session state
        and returns a redirect response to the URL provided by its helper.
        """

        dummy_state = "test-csrf-state-token-123"
        dummy_redirect_url = "https://oauth.provider.com/auth?state=...&client_id=..."

        mock_get_redirection_url.return_value = (dummy_state, dummy_redirect_url)

        response = self.client.get("/login", follow_redirects=False)

        mock_get_redirection_url.assert_called_once_with(self.mock_oauth_service)

        self.assertEqual(response.status_code, status.HTTP_307_TEMPORARY_REDIRECT)

        self.assertEqual(response.headers["location"], dummy_redirect_url)

    @patch("material_ai.api.remove_token", new_callable=AsyncMock)
    async def test_logout_with_refresh_token(self, mock_remove_token, mock_get_config):
        """
        Tests that /logout calls remove_token with the token from the cookie.
        """

        # --- Act ---
        # 2. Make the GET request to the /logout endpoint, passing the cookie.
        response = self.client.get("/logout")

        # --- Assert ---
        # 3. Verify the response status code is correct.
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 4. Verify that our mocked remove_token function was awaited exactly once.
        mock_remove_token.assert_awaited_once()

        # 5. Check that remove_token was called with the correct arguments.
        # We use ANY for the response object because it's created inside the endpoint.
        mock_remove_token.assert_awaited_once_with(
            ANY, self.cookies["refresh_token"], self.mock_oauth_service
        )

    @patch("material_ai.api.remove_token", new_callable=AsyncMock)
    async def test_logout_without_refresh_token(
        self, mock_remove_token, mock_get_config
    ):
        """
        Tests that /logout calls remove_token with None when no cookie is present.
        """
        # --- Arrange ---
        # (No token or cookies are needed for this test case)

        # --- Act ---
        # Make the GET request without sending any cookies.
        response = self.client.get("/logout")

        # --- Assert ---
        # Verify the status code.
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify that remove_token was still called.
        mock_remove_token.assert_awaited_once()

    def test_submit_feedback_success(self, mock_get_config):
        """
        Tests successful feedback submission with a valid payload.
        """

        feedback_payload = {
            "feedback_category": "GOOD",
            "feedback_text": "This was very helpful!",
            "id": "12345",
        }

        expected_response = {"status": "feedback logged successfully"}
        self.mock_feedback_handler.return_value = expected_response

        response = self.client.post("/feedback", json=feedback_payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json(), expected_response)

        self.mock_feedback_handler.assert_awaited_once()
        call_args, _ = self.mock_feedback_handler.call_args
        sent_feedback_object = call_args[0]
        self.assertIsInstance(sent_feedback_object, FeedbackRequest)
        self.assertEqual(
            sent_feedback_object.feedback_category,
            feedback_payload["feedback_category"],
        )
        self.assertEqual(
            sent_feedback_object.feedback_text, feedback_payload["feedback_text"]
        )

    def test_submit_feedback_invalid_payload(self, mock_get_config):
        """
        Tests feedback submission with a missing required field,
        expecting a 422 Validation Error.
        """
        invalid_payload = {"text": "This is missing the value."}

        response = self.client.post("/feedback", json=invalid_payload)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_CONTENT)

        self.mock_feedback_handler.assert_not_awaited()

    def test_root_serves_index_html(self, mock_get_config):
        """
        Tests that the root endpoint '/' correctly calls FileResponse
        with the path to index.html.
        """
        # Arrange: Define the expected path that the function should construct.
        expected_path = os.path.join(STATIC_DIR, "index.html")

        # Act: Make a request to the root endpoint.
        self.client.get("/")

        # Assert: Verify that the mocked FileResponse class was instantiated
        # exactly once with the correct path and media type.
        self.mock_file_response.assert_called_once_with(
            path=expected_path, media_type="text/html"
        )

    @patch("material_ai.api.psutil")
    def test_health_check_returns_system_metrics(self, mock_psutil, mock_get_config):
        """
        Verify that the /health endpoint correctly formats and returns
        system metrics from mocked dependencies.
        """
        # --- Arrange: Configure the mocks to return predictable data ---

        # Mock the config object
        mock_config = MagicMock()
        mock_config.general.debug = True
        mock_get_config.return_value = mock_config

        # Mock psutil functions and their return values
        mock_psutil.cpu_percent.return_value = 55.5

        # Mock the return object for virtual_memory()
        mock_mem = MagicMock()
        mock_mem.total = 16 * (1024**3)  # 16 GB
        mock_mem.available = 4 * (1024**3)  # 4 GB
        mock_mem.percent = 75.0
        mock_psutil.virtual_memory.return_value = mock_mem

        # Mock the return object for disk_usage()
        mock_disk = MagicMock()
        mock_disk.total = 512 * (1024**3)  # 512 GB
        mock_disk.used = 128 * (1024**3)  # 128 GB
        mock_disk.free = 384 * (1024**3)  # 384 GB
        mock_disk.percent = 25.0
        mock_psutil.disk_usage.return_value = mock_disk

        # --- Act: Make a request to the endpoint ---
        response = self.client.get("/health")

        # --- Assert: Check the response ---
        self.assertEqual(response.status_code, 200)

        data = response.json()

        # Check top-level fields
        self.assertEqual(data["status"], "ok")
        self.assertTrue("uptime" in data)  # Check for uptime existence
        self.assertTrue(data["debug"])

        # Check nested system metrics
        expected_system_data = {
            "cpu_percent_used": 55.5,
            "memory": {
                "total": "16.00 GB",
                "available": "4.00 GB",
                "percent_used": 75.0,
            },
            "disk": {
                "total": "512.00 GB",
                "used": "128.00 GB",
                "free": "384.00 GB",
                "percent_used": 25.0,
            },
        }
        self.assertEqual(data["system"], expected_system_data)

    # Test for config()
    def test_config(self, mock_get_config):
        """Should return the mocked UI configuration."""
        response = self.client.get("/config")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("title"), self.mock_ui_config.title)
        self.assertEqual(response.json().get("greeting"), self.mock_ui_config.greeting)
        self.assertEqual(
            response.json().get("errorMessage"), self.mock_ui_config.errorMessage
        )

    def test_api_without_cookies(self, mock_get_config):

        invalid_payload = {"text": "This is missing the value."}

        self.client.cookies = None

        response = self.client.post("/feedback", json=invalid_payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.mock_feedback_handler.assert_not_awaited()

    def test_api_without_access_token(self, mock_get_config):

        invalid_payload = {"text": "This is missing the value."}

        self.client.cookies = {
            "refresh_token": "test_refresh_token",
            "user_details": "test_user_details",
        }

        response = self.client.post("/feedback", json=invalid_payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.mock_feedback_handler.assert_not_awaited()

    def test_api_without_user_details(self, mock_get_config):

        invalid_payload = {"text": "This is missing the value."}

        self.client.cookies = {
            "refresh_token": "test_refresh_token",
            "access_token": "test_user_details",
        }

        response = self.client.post("/feedback", json=invalid_payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.mock_feedback_handler.assert_not_awaited()

    def test_api_with_invaid_oauth_service(self, mock_get_config):

        self.mock_oauth_service.sso_verify_access_token.return_value = None

        response = self.client.get("/logout")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_api_with_error_oauth_service(self, mock_get_config):

        self.mock_oauth_service.sso_verify_access_token.return_value = (
            OAuthErrorResponse(status_code=401, detail="SomeErrorHasOccured")
        )

        response = self.client.get("/logout")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("material_ai.middleware.auth_middleware.verify_user_details")
    def test_api_with_users_and_invalid_user(
        self, mock_verify_user_details, mock_get_config
    ):

        mock_verify_user_details.return_value = None
        response = self.client.post("/run")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("material_ai.middleware.auth_middleware.verify_user_details")
    def test_api_with_users_and_invalid_uid(
        self, mock_verify_user_details, mock_get_config
    ):
        user_detail = OAuthUserDetail(
            sub="12345",
            name="Fresh User",
            given_name="Fresh User",
            family_name="Fresh User",
            picture="Test pitcure",
            email="test@test.com",
            email_verified=True,
        )
        mock_verify_user_details.return_value = user_detail.model_dump_json()
        response = self.client.post("/run", json={"user_id": "test_user_1234"})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("material_ai.middleware.auth_middleware.verify_user_details")
    def test_api_with_users_and_valid_uid(
        self, mock_verify_user_details, mock_get_config
    ):
        user_detail = OAuthUserDetail(
            sub="test_user_123",
            name="Fresh User",
            given_name="Fresh User",
            family_name="Fresh User",
            picture="Test pitcure",
            email="test@test.com",
            email_verified=True,
        )
        mock_verify_user_details.return_value = user_detail.model_dump_json()
        response = self.client.post("/run", json={"user_id": "test_user_123"})

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_CONTENT)

    def test_api_with_users_and_invalid_uid(self, mock_get_config):

        response = self.client.get("sessions/12345/users/12345")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


def create_dummy_ui_config() -> UIConfig:
    return UIConfig(
        title="Test",
        greeting="Test greeting",
        errorMessage="Test error message",
        models=[
            {"model": "Test Model 1", "tagline": "Test tagline 1"},
            {"model": "Test Model 2", "tagline": "Test tagline 2"},
        ],
        feedback={
            "positive": {"value": "GOOD", "categories": []},
            "negative": {"value": "BAD", "categories": []},
        },
        theme={
            "lightPalette": {
                "mode": "light",
                "primary": {"main": ""},
                "background": {
                    "default": "",
                    "paper": "",
                    "card": "",
                    "cardHover": "",
                    "history": "",
                },
                "text": {
                    "primary": "",
                    "secondary": "",
                    "tertiary": "",
                    "h5": "",
                    "selected": "",
                    "tagline": "",
                },
                "tooltip": {"background": "", "text": ""},
            },
            "darkPalette": {
                "mode": "dark",
                "primary": {"main": ""},
                "background": {
                    "default": "",
                    "paper": "",
                    "card": "",
                    "cardHover": "",
                    "history": "",
                },
                "text": {
                    "primary": "",
                    "secondary": "",
                    "tertiary": "",
                    "h5": "",
                    "selected": "",
                    "tagline": "",
                },
                "tooltip": {"background": "", "text": ""},
            },
        },
    )


def create_dummy_config(debug_mode: bool = True) -> Config:
    return Config(
        sso=SSOConfig(
            session_secret_key="a-fake-but-valid-secret-key-for-testing",
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="test_redirect_uri",
        ),
        general=GeneralConfig(debug=debug_mode),
        adk=ADKConfig(
            session_db_url="sqlite:///./test_sessions.db",
        ),
        google=GoogleConfig(
            genai_use_vertexai="true", api_key="fake-google-api-key-12345"
        ),
    )
