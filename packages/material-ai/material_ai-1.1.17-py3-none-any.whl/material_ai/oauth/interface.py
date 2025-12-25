from abc import ABC, abstractmethod
from .schema import OAuthRedirectionResponse, OAuthSuccessResponse, OAuthErrorResponse
from .schema import SSOConfig, OAuthUserDetail


class IOAuthService(ABC):
    """
    Abstract Base Class (Interface) defining the contract for any
    OAuth 2.0 or OpenID Connect service implementation (e.g., Google, GitHub).

    Any concrete class inheriting from IOAuthService must implement all
    abstract methods to handle the complete OAuth flow, including
    redirection, callback processing, and user detail retrieval.
    """

    @abstractmethod
    def sso_get_redirection_url(self, sso: SSOConfig) -> OAuthRedirectionResponse:
        """Generates the provider-specific URL for user redirection.

        This URL starts the OAuth 2.0 authorization flow, prompting the
        user to grant consent to the application.

        Args:
            sso: An SSOConfig object containing the configuration details
                 like client ID, scopes, and redirect URI.

        Returns:
            An OAuthRedirectionResponse object containing the generated
            authorization URL.
        """
        pass

    @abstractmethod
    async def sso_get_access_token(
        self, sso: SSOConfig, authorization_code: str
    ) -> OAuthSuccessResponse | OAuthErrorResponse:
        """Exchanges an authorization code for an access and refresh token.

        This method is called after the user is redirected back from the
        OAuth provider with an authorization code.

        Args:
            sso: The SSOConfig object with provider details.
            authorization_code: The code provided by the OAuth server
                                as a query parameter.

        Returns:
            An OAuthSuccessResponse with token details on success,
            or an OAuthErrorResponse on failure.
        """
        pass

    @abstractmethod
    async def sso_get_new_access_token(
        self, sso: SSOConfig, refresh_token: str
    ) -> OAuthSuccessResponse | OAuthErrorResponse:
        """Obtains a new access token using a refresh token.

        This is used to get a new access token when the current one expires,
        without requiring the user to log in again.

        Args:
            sso: The SSOConfig object with provider details.
            refresh_token: The refresh token issued during the initial
                           token exchange.

        Returns:
            An OAuthSuccessResponse with the new access token on success,
            or an OAuthErrorResponse on failure.
        """
        pass

    @abstractmethod
    async def sso_get_user_details(
        self, sso: SSOConfig, access_token: str
    ) -> OAuthUserDetail | OAuthErrorResponse:
        """Fetches user profile information from the OAuth provider.

        Args:
            sso: The SSOConfig object with provider details.
            access_token: A valid access token for the user.

        Returns:
            An OAuthUserDetail object with the user's information on success,
            or an OAuthErrorResponse on failure.
        """
        pass

    @abstractmethod
    async def sso_revoke_refresh_token(
        self, refresh_token: str
    ) -> None | OAuthErrorResponse:
        """Revokes a refresh token, invalidating it.

        This is typically used during a sign-out process to ensure the
        token can no longer be used to generate new access tokens.

        Args:
            refresh_token: The refresh token to be revoked.

        Returns:
            None on successful revocation, or an OAuthErrorResponse
            if an error occurs.
        """
        pass

    @abstractmethod
    async def sso_verify_access_token(
        self, access_token: str
    ) -> str | OAuthErrorResponse:
        """Verifies the validity of an access token.

        Checks with the OAuth provider to confirm if the token is active
        and not expired or revoked.

        Args:
            access_token: The access token to verify.

        Returns:
            String uid if the token is valid, None if it's invalid, or an
            OAuthErrorResponse if an error occurs during verification.
        """
        pass
