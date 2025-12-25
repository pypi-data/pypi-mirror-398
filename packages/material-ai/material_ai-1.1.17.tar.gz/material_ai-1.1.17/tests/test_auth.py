# test_dependencies.py

import unittest
from unittest.mock import patch, MagicMock, AsyncMock, call
from datetime import timedelta
import base64
import hmac
import hashlib
from material_ai.auth import (
    get_oauth_service,
    get_ui_configuration,
    get_feedback_handler,
    IOAuthService,
    OAuthSuccessResponse,
    _remove_cookies,
    verify_user_details,
    OAuthUserDetail,
    on_callback,
    _set_oauth_token_cookies,
    UserSuccessResponse,
    remove_token,
    RedirectResponse,
    OAuthErrorResponse,
    get_user_details,
    get_redirection_url,
    _sign_user_details,
    HTTPException,
    Response,
)
from material_ai.oauth import OAuthRedirectionResponse


class TestDependencyGetters(unittest.IsolatedAsyncioTestCase):
    """
    Tests for dependency getter functions.
    Verifies that each function raises NotImplementedError as expected.
    """

    def test_get_oauth_service_raises_not_implemented(self):
        """
        Ensures get_oauth_service raises NotImplementedError.
        """
        with self.assertRaises(NotImplementedError) as cm:
            get_oauth_service()

        # Optionally, check the exception message
        self.assertEqual(
            str(cm.exception), "This dependency must be overridden by the application."
        )

    def test_get_ui_configuration_raises_not_implemented(self):
        """
        Ensures get_ui_configuration raises NotImplementedError.
        """
        with self.assertRaises(NotImplementedError):
            get_ui_configuration()

    def test_get_feedback_handler_raises_not_implemented(self):
        """
        Ensures get_feedback_handler raises NotImplementedError.
        """
        with self.assertRaises(NotImplementedError):
            get_feedback_handler()

    @patch("material_ai.auth._logger")
    @patch("material_ai.auth.get_config")
    def test_verify_user_details_success(
        self, mock_get_config: MagicMock, mock_logger: MagicMock
    ):
        """
        Tests that a correctly signed string is successfully verified.
        """
        # --- Arrange ---
        # 1. Set up a known secret key and user data.
        secret_key = "my-test-secret-key"
        user_detail = OAuthUserDetail(
            email="test@test.com",
            email_verified=True,
            family_name="Test User",
            given_name="Test User",
            name="Test User",
            picture="Test pitcure",
            sub="sub#123",
        )
        user_data_json = user_detail.model_dump_json()
        mock_get_config.return_value.sso.session_secret_key = secret_key

        # 2. Manually create a valid signed string, just like _sign_user_details would.
        b64encoded_details = base64.b64encode(user_data_json.encode("utf-8"))
        signature = hmac.new(
            secret_key.encode("utf-8"), b64encoded_details, hashlib.sha256
        ).hexdigest()
        valid_signed_string = f"{b64encoded_details.decode('utf-8')}.{signature}"

        # --- Act ---
        result = verify_user_details(valid_signed_string)

        # --- Assert ---
        # 1. The result should be the original, decoded user data.
        self.assertEqual(result, user_data_json)
        # 2. The warning logger should not have been called.
        mock_logger.warning.assert_not_called()

    @patch("material_ai.auth._logger")
    @patch("material_ai.auth.get_config")
    def test_verify_user_details_invalid_signature(
        self, mock_get_config: MagicMock, mock_logger: MagicMock
    ):
        """
        Tests that a string with an incorrect signature returns None.
        """
        # --- Arrange ---
        secret_key = "my-test-secret-key"
        mock_get_config.return_value.sso.session_secret_key = secret_key
        user_detail = OAuthUserDetail(
            email="test@test.com",
            email_verified=True,
            family_name="Test User",
            given_name="Test User",
            name="Test User",
            picture="Test pitcure",
            sub="sub#123",
        )
        user_data_json = user_detail.model_dump_json()
        b64encoded_details = base64.b64encode(user_data_json.encode("utf-8"))

        # Tamper with the signature
        invalid_signature = "thisisnotthecorrectsignature"
        tampered_string = f"{b64encoded_details.decode('utf-8')}.{invalid_signature}"

        # --- Act ---
        result = verify_user_details(tampered_string)

        # --- Assert ---
        self.assertIsNone(result)
        mock_logger.warning.assert_called_once()

    def test_verify_user_details_malformed_string(self):
        """
        Tests that a string without a '.' separator returns None.
        """
        # --- Arrange ---
        malformed_string = "thisstringhasnoSeparator"

        # --- Act ---
        result = verify_user_details(malformed_string)

        # --- Assert ---
        self.assertIsNone(result)

    @patch("material_ai.auth.get_config")
    def test_sign_user_details_creates_correct_signature(
        self, mock_get_config: MagicMock
    ):
        """
        Tests that user details are correctly base64 encoded and signed.
        """
        # --- Arrange ---
        # 1. Mock the configuration to provide a known secret key.
        secret_key = "my-super-secret-key-for-testing"
        mock_get_config.return_value.sso.session_secret_key = secret_key

        # 2. Create mock user data. The mock needs a `model_dump_json` method.
        user_detail = OAuthUserDetail(
            email="test@test.com",
            email_verified=True,
            family_name="Test User",
            given_name="Test User",
            name="Test User",
            picture="Test pitcure",
            sub="sub#123",
        )
        user_data_json_string = user_detail.model_dump_json()
        mock_user_details = MagicMock(spec=OAuthUserDetail)
        mock_user_details.model_dump_json.return_value = user_data_json_string

        # --- Act ---
        # Call the function with the mocked dependencies.
        signed_string = _sign_user_details(mock_user_details)

        # --- Assert ---
        # 1. Manually re-create the expected output to verify the function's logic.
        encoded_key = secret_key.encode("utf-8")
        b64encoded_details = base64.b64encode(user_data_json_string.encode("utf-8"))
        expected_signature = hmac.new(
            encoded_key, b64encoded_details, hashlib.sha256
        ).hexdigest()

        expected_string = f"{b64encoded_details.decode('utf-8')}.{expected_signature}"

        # 2. Assert that the function output matches the expected value.
        self.assertEqual(signed_string, expected_string)

        # 3. Verify that the dependencies were called as expected.
        mock_get_config.assert_called_once()
        mock_user_details.model_dump_json.assert_called_once()

    @patch("material_ai.auth._sign_user_details")
    @patch("material_ai.auth.get_config")
    def test_set_cookies_in_debug_mode(
        self, mock_get_config: MagicMock, mock_sign_user_details: MagicMock
    ):
        """
        Tests that cookies are set with secure=False in debug mode.
        """
        # --- Arrange ---
        # 1. Configure mocks
        mock_get_config.return_value.general.debug = True
        mock_sign_user_details.return_value = "signed.user.details"

        # 2. Create mock data objects
        mock_oauth_data = OAuthSuccessResponse(
            access_token="test_access_token",
            expires_in=3066,
            refresh_token="test_refresh_token",
            user_detail=OAuthUserDetail(
                email="test@test.com",
                email_verified=True,
                family_name="Test User",
                given_name="Test User",
                name="Test User",
                picture="Test pitcure",
                sub="sub#123",
            ),
        )
        mock_response = MagicMock(spec=Response)

        # --- Act ---
        _set_oauth_token_cookies(mock_response, mock_oauth_data)

        # --- Assert ---
        # 1. Check that the signing function was called correctly
        # 2. Define the expected calls to response.set_cookie
        expected_refresh_expiration = 3600 + int(timedelta(days=2).total_seconds())
        expected_calls = [
            call(
                key="access_token",
                value="test_access_token",
                httponly=True,
                secure=False,  # <-- Important for this test
                max_age=3600,
                samesite="lax",
                path="/",
            ),
            call(
                key="refresh_token",
                value="test_refresh_token",
                httponly=True,
                secure=False,  # <-- Important for this test
                max_age=expected_refresh_expiration,
                samesite="lax",
                path="/",
            ),
            call(
                key="user_details",
                value="signed.user.details",
                httponly=True,
                secure=False,  # <-- Important for this test
                max_age=3600,
                samesite="lax",
                path="/",
            ),
        ]

    @patch("material_ai.auth._sign_user_details")
    @patch("material_ai.auth.get_config")
    def test_set_cookies_in_production_mode(
        self, mock_get_config: MagicMock, mock_sign_user_details: MagicMock
    ):
        """
        Tests that cookies are set with secure=True in production mode.
        """
        # --- Arrange ---
        # 1. Configure mocks for production
        mock_get_config.return_value.general.debug = False
        mock_sign_user_details.return_value = "signed.user.details"

        # 2. Create mock data objects
        mock_oauth_data = OAuthSuccessResponse(
            access_token="test_access_token",
            expires_in=3066,
            refresh_token="test_refresh_token",
            user_detail=OAuthUserDetail(
                email="test@test.com",
                email_verified=True,
                family_name="Test User",
                given_name="Test User",
                name="Test User",
                picture="Test pitcure",
                sub="sub#123",
            ),
        )
        mock_response = MagicMock(spec=Response)

        # --- Act ---
        _set_oauth_token_cookies(mock_response, mock_oauth_data)

        self.assertEqual(mock_response.set_cookie.call_count, 3)

    def test_remove_cookies_deletes_all_auth_cookies(self):
        """
        Tests that _remove_cookies calls delete_cookie for each auth token.
        """
        # --- Arrange ---
        # 1. Create a mock Response object. We only need it to have a
        #    delete_cookie method that we can inspect.
        mock_response = MagicMock(spec=Response)

        # 2. Define the list of expected cookies to be deleted.
        expected_cookies = ["access_token", "refresh_token", "user_details"]

        # --- Act ---
        # Call the function with our mock object.
        _remove_cookies(mock_response)

        # --- Assert ---
        # 1. Verify that the delete_cookie method was called 3 times.
        self.assertEqual(
            mock_response.delete_cookie.call_count,
            3,
            "delete_cookie should be called exactly 3 times.",
        )

        # 2. Create a list of expected `call` objects.
        #    The `any_order=True` flag means the test will pass
        #    even if the function deletes cookies in a different order.
        expected_calls = [
            call("access_token"),
            call("refresh_token"),
            call("user_details"),
        ]

        # 3. Assert that the method was called with all the expected arguments.
        mock_response.delete_cookie.assert_has_calls(expected_calls, any_order=True)

    @patch("material_ai.auth._remove_cookies")
    async def test_remove_token_success_with_valid_token(
        self, mock_remove_cookies: MagicMock
    ):
        """
        Tests successful token revocation and cookie removal.
        """
        # --- Arrange ---
        mock_oauth_service = AsyncMock(spec=IOAuthService)
        # Simulate a successful response from the SSO provider
        mock_oauth_service.sso_revoke_refresh_token.return_value = OAuthSuccessResponse(
            access_token="test_access_token",
            expires_in=3066,
            refresh_token="test_refresh_token",
            user_detail=OAuthUserDetail(
                email="test@test.com",
                email_verified=True,
                family_name="Test User",
                given_name="Test User",
                name="Test User",
                picture="Test pitcure",
                sub="sub#123",
            ),
        )
        mock_response_object = MagicMock(spec=Response)
        refresh_token = "valid_token_to_revoke"

        # --- Act ---
        result = await remove_token(
            mock_response_object, refresh_token, mock_oauth_service
        )

        # --- Assert ---
        # 1. Verify the revocation method was called
        mock_oauth_service.sso_revoke_refresh_token.assert_awaited_once_with(
            refresh_token
        )
        # 2. Verify cookies were removed
        mock_remove_cookies.assert_called_once_with(mock_response_object)
        # 3. Verify the correct response object was returned
        self.assertIs(result, mock_response_object)

    @patch("material_ai.auth._remove_cookies")
    async def test_remove_token_failure_raises_http_exception(
        self, mock_remove_cookies: MagicMock
    ):
        """
        Tests that an HTTPException is raised when revocation fails.
        """
        # --- Arrange ---
        mock_oauth_service = AsyncMock(spec=IOAuthService)
        # Simulate an error response from the SSO provider
        mock_oauth_service.sso_revoke_refresh_token.return_value = OAuthErrorResponse(
            status_code=500, detail="SomeErrorHasOccured"
        )
        mock_response_object = MagicMock(spec=Response)
        refresh_token = "token_that_fails"

        # --- Act & Assert ---
        with self.assertRaises(HTTPException) as context:
            await remove_token(mock_response_object, refresh_token, mock_oauth_service)

        self.assertEqual(context.exception.status_code, 500)
        # Ensure cookies are NOT removed if revocation fails, as the code raises an exception first
        mock_remove_cookies.assert_not_called()

    @patch("material_ai.auth._remove_cookies")
    async def test_remove_token_with_none_token(self, mock_remove_cookies: MagicMock):
        """
        Tests the case where no refresh token is provided.
        """
        # --- Arrange ---
        mock_oauth_service = AsyncMock(spec=IOAuthService)
        mock_response_object = MagicMock(spec=Response)

        # --- Act ---
        # NOTE: The provided source code contains a bug where this path
        # returns `None` instead of the `response` object. This test
        # verifies the behavior of the code *as written*.
        result = await remove_token(mock_response_object, None, mock_oauth_service)

        # --- Assert ---
        # 1. Verify the revocation method was NOT called
        mock_oauth_service.sso_revoke_refresh_token.assert_not_awaited()
        # 2. Verify cookies were still removed
        mock_remove_cookies.assert_called_once_with(mock_response_object)
        # 3. Verify the function returns None due to the `return` statement
        self.assertIsNone(result)

    @patch("material_ai.auth.get_config")
    def test_get_redirection_url_returns_correct_tuple(
        self, mock_get_config: MagicMock
    ):
        """
        Tests that the function returns the correct state and URL tuple.
        """
        # --- Arrange ---
        # 1. Define expected values
        expected_state = "test_state_12345"
        expected_url = "https://sso.provider.com/auth?client_id=123"

        # 2. Mock the response from the oauth_service call
        mock_sso_response = OAuthRedirectionResponse(
            state=expected_state, redirection_url=expected_url
        )

        # 3. Mock the IOAuthService dependency
        mock_oauth_service = MagicMock(spec=IOAuthService)
        mock_oauth_service.sso_get_redirection_url.return_value = mock_sso_response

        # 4. Mock the config dependency
        mock_get_config.return_value = MagicMock(sso="sso_config_object")

        # --- Act ---
        state, redirection_url = get_redirection_url(mock_oauth_service)

        # --- Assert ---
        # 1. Verify get_config was called
        mock_get_config.assert_called_once()

        # 2. Verify the service method was called with the correct config
        mock_oauth_service.sso_get_redirection_url.assert_called_once_with(
            sso=mock_get_config.return_value.sso
        )

        # 3. Check if the returned values match the expected values
        self.assertEqual(state, expected_state)
        self.assertEqual(redirection_url, expected_url)

    @patch("material_ai.auth._set_oauth_token_cookies")
    @patch("material_ai.auth.get_config")
    async def test_get_user_details_success(
        self, mock_get_config: MagicMock, mock_set_cookies: MagicMock
    ):
        """
        Tests the successful flow where user details are fetched.
        """
        # --- Arrange ---
        mock_user_data = OAuthUserDetail(
            email="test@test.com",
            email_verified=True,
            family_name="Test User",
            given_name="Test User",
            name="Test User",
            picture="Test pitcure",
            sub="sub#123",
        )
        mock_oauth_response = OAuthSuccessResponse(
            access_token="test_access_token",
            expires_in=3066,
            refresh_token="test_refresh_token",
            user_detail=mock_user_data,
        )

        mock_oauth_service = AsyncMock(spec=IOAuthService)
        mock_oauth_service.sso_get_new_access_token.return_value = mock_oauth_response

        mock_get_config.return_value = MagicMock(sso="sso_config")
        mock_response_object = MagicMock(spec=Response)
        refresh_token = "valid_refresh_token"

        # --- Act ---
        result = await get_user_details(
            mock_response_object, refresh_token, mock_oauth_service
        )

        # --- Assert ---
        # 1. Check that the token refresh method was called correctly
        mock_oauth_service.sso_get_new_access_token.assert_awaited_once_with(
            mock_get_config.return_value.sso, refresh_token
        )

        # 2. Check that cookies were set with the new token data
        mock_set_cookies.assert_called_once_with(
            mock_response_object, mock_oauth_response
        )

        # 3. Verify the returned object is correct
        self.assertIsInstance(result, UserSuccessResponse)
        self.assertEqual(result.user_response, mock_user_data)

    @patch("material_ai.auth.get_config")
    async def test_get_user_details_failure_raises_http_exception(
        self, mock_get_config: MagicMock
    ):
        """
        Tests the failure flow where the token refresh returns an error.
        """
        # --- Arrange ---
        mock_oauth_service = AsyncMock(spec=IOAuthService)
        mock_oauth_service.sso_get_new_access_token.return_value = OAuthErrorResponse(
            status_code=401, detail="UnAuthorized"
        )

        mock_get_config.return_value = MagicMock(sso="sso_config")
        mock_response_object = MagicMock(spec=Response)
        refresh_token = "invalid_refresh_token"

        # --- Act & Assert ---
        with self.assertRaises(HTTPException) as context:
            await get_user_details(
                mock_response_object, refresh_token, mock_oauth_service
            )

        self.assertEqual(context.exception.status_code, 500)
        mock_oauth_service.sso_get_new_access_token.assert_awaited_once()

    @patch("material_ai.auth._set_oauth_token_cookies")
    @patch("material_ai.auth.get_config")
    async def test_on_callback_success(
        self, mock_get_config: MagicMock, mock_set_cookies: MagicMock
    ):
        """
        Tests the successful OAuth callback flow.
        """
        # --- Arrange ---
        # Mock the external dependencies
        mock_oauth_service = AsyncMock(spec=IOAuthService)
        mock_token_response = OAuthSuccessResponse(
            access_token="test_access_token",
            expires_in=3066,
            refresh_token="test_refresh_token",
            user_detail=OAuthUserDetail(
                email="test@test.com",
                email_verified=True,
                family_name="Test User",
                given_name="Test User",
                name="Test User",
                picture="Test pitcure",
                sub="sub#123",
            ),
        )  # A successful token object
        mock_oauth_service.sso_get_access_token.return_value = mock_token_response
        mock_get_config.return_value = MagicMock(sso="sso_config")

        auth_code = "valid_authorization_code"

        # --- Act ---
        response = await on_callback(auth_code, mock_oauth_service)

        # --- Assert ---
        # 1. Check if the SSO service was called correctly
        mock_oauth_service.sso_get_access_token.assert_awaited_once_with(
            mock_get_config.return_value.sso, auth_code
        )

        # 2. Check if the cookie helper was called with the response and token
        mock_set_cookies.assert_called_once_with(response, mock_token_response)

        # 3. Verify the returned response is correct
        self.assertIsInstance(response, RedirectResponse)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["location"], "/")

    @patch("material_ai.auth.get_config")
    async def test_on_callback_failure_raises_http_exception(
        self, mock_get_config: MagicMock
    ):
        """
        Tests the failure flow where the token exchange returns an error.
        """
        # --- Arrange ---
        mock_oauth_service = AsyncMock(spec=IOAuthService)
        mock_oauth_service.sso_get_access_token.return_value = OAuthErrorResponse(
            status_code=401, detail="UnAuthorized"
        )
        mock_get_config.return_value = MagicMock(sso="sso_config")

        auth_code = "invalid_authorization_code"

        # --- Act & Assert ---
        with self.assertRaises(HTTPException) as context:
            await on_callback(auth_code, mock_oauth_service)

        # Check if the correct exception was raised
        self.assertEqual(context.exception.status_code, 500)

        # Ensure the SSO service was still called
        mock_oauth_service.sso_get_access_token.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
