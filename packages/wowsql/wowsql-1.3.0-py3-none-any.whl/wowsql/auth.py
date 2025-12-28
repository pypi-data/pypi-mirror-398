"""Project-level authentication client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

import requests

from .client import WowSQLError


@dataclass
class AuthUser:
    """Represents an authenticated user."""

    id: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    email_verified: bool = False
    user_metadata: Dict[str, Any] = None
    app_metadata: Dict[str, Any] = None
    created_at: Optional[str] = None


@dataclass
class AuthSession:
    """Session tokens returned by the auth service."""

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


@dataclass
class AuthResponse:
    """Response for signup/login requests."""

    session: AuthSession
    user: Optional[AuthUser] = None


class TokenStorage(Protocol):
    """Interface for persisting tokens."""

    def get_access_token(self) -> Optional[str]:
        ...

    def set_access_token(self, token: Optional[str]) -> None:
        ...

    def get_refresh_token(self) -> Optional[str]:
        ...

    def set_refresh_token(self, token: Optional[str]) -> None:
        ...


class MemoryTokenStorage:
    """Default in-memory token storage."""

    def __init__(self) -> None:
        self._access: Optional[str] = None
        self._refresh: Optional[str] = None

    def get_access_token(self) -> Optional[str]:
        return self._access

    def set_access_token(self, token: Optional[str]) -> None:
        self._access = token

    def get_refresh_token(self) -> Optional[str]:
        return self._refresh

    def set_refresh_token(self, token: Optional[str]) -> None:
        self._refresh = token


class ProjectAuthClient:
    """
    Client for project-level AUTHENTICATION endpoints.
    
    UNIFIED AUTHENTICATION: Uses the same API keys (anon/service) as database operations.
    One project = one set of keys for ALL operations (auth + database).
    
    Key Types:
        - Anonymous Key (wowsql_anon_...): For client-side auth operations (signup, login, OAuth)
        - Service Role Key (wowsql_service_...): For server-side auth operations (admin, full access)
    
    Example:
        >>> auth = ProjectAuthClient(
        ...     project_url="myproject",
        ...     api_key="wowsql_anon_..."  # Use anon key for client-side, service key for server-side
        ... )
        >>> url = auth.get_oauth_authorization_url(provider="github")
    """

    def __init__(
        self,
        project_url: str,
        *,
        base_domain: str = "wowsql.com",
        secure: bool = True,
        timeout: int = 30,
        verify_ssl: bool = True,
        api_key: Optional[str] = None,
        public_api_key: Optional[str] = None,  # Deprecated: use api_key instead
        token_storage: Optional[TokenStorage] = None,
        session: Optional[requests.Session] = None,
    ) -> None:
        """
        Initialize ProjectAuthClient for AUTHENTICATION OPERATIONS.
        
        UNIFIED AUTHENTICATION: Uses the same API keys (anon/service) as database operations.
        
        Args:
            project_url: Project subdomain or full URL
            api_key: Unified API key - Anonymous Key (wowsql_anon_...) for client-side,
                    or Service Role Key (wowsql_service_...) for server-side.
                    This same key works for both auth and database operations.
            public_api_key: Deprecated - use api_key instead. Kept for backward compatibility.
            base_domain: Base domain (default: wowsql.com)
            secure: Use HTTPS (default: True)
            timeout: Request timeout in seconds (default: 30)
            verify_ssl: Verify SSL certificates (default: True)
            token_storage: Optional token storage for persisting access/refresh tokens
            session: Optional requests.Session for custom HTTP configuration
        
        Note:
            - Use Anonymous Key (wowsql_anon_...) for client-side/public auth flows
            - Use Service Role Key (wowsql_service_...) for server-side/admin operations
            - Same keys work for both auth and database operations (unified authentication)
        """
        # Support both api_key (new) and public_api_key (deprecated) for backward compatibility
        unified_api_key = api_key or public_api_key
        
        self.base_url = _build_auth_base_url(project_url, base_domain, secure)
        self.timeout = timeout
        self.api_key = unified_api_key
        self.public_api_key = unified_api_key  # Keep for backward compatibility

        self.session = session or requests.Session()
        self.session.verify = verify_ssl
        self.session.headers.update({"Content-Type": "application/json"})
        if unified_api_key:
            # UNIFIED AUTHENTICATION: Use Authorization header (same as database operations)
            self.session.headers["Authorization"] = f"Bearer {unified_api_key}"

        self.storage = token_storage or MemoryTokenStorage()
        self._access_token = self.storage.get_access_token()
        self._refresh_token = self.storage.get_refresh_token()

        if not verify_ssl:
            import urllib3

            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # -------------------------- Public API -------------------------- #

    def sign_up(
        self,
        *,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        user_metadata: Optional[Dict[str, Any]] = None,
    ) -> AuthResponse:
        payload = {
            "email": email,
            "password": password,
            "full_name": full_name,
            "user_metadata": user_metadata,
        }
        data = self._request("POST", "/signup", json=payload)
        session = self._persist_session(data)
        user = AuthUser(**_normalize_user(data.get("user"))) if data.get("user") else None
        return AuthResponse(session=session, user=user)

    def sign_in(self, *, email: str, password: str) -> AuthResponse:
        payload = {"email": email, "password": password}
        data = self._request("POST", "/login", json=payload)
        session = self._persist_session(data)
        return AuthResponse(session=session, user=None)

    def get_user(self, access_token: Optional[str] = None) -> AuthUser:
        token = access_token or self._access_token or self.storage.get_access_token()
        if not token:
            raise WowSQLError("Access token is required. Call sign_in first.")

        data = self._request(
            "GET",
            "/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        return AuthUser(**_normalize_user(data))

    def get_oauth_authorization_url(
        self,
        provider: str,
        *,
        redirect_uri: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Get OAuth authorization URL for the specified provider.
        
        Uses backend callback pattern: GitHub redirects to backend, backend redirects to frontend.
        
        Args:
            provider: OAuth provider name (e.g., 'github', 'google', 'facebook', 'microsoft')
            redirect_uri: Optional frontend redirect URI where user will land after OAuth completes.
                         If not provided, backend will use configured default frontend URL.
                         This is NOT the GitHub callback URL - GitHub will redirect to backend.
        
        Returns:
            Dict containing:
                - authorization_url: The URL to redirect the user to for OAuth authorization
                - provider: The provider name
                - backend_callback_url: The backend callback URL (registered in GitHub)
                - frontend_redirect_uri: The frontend URL where user will land after auth
        
        Raises:
            WowSQLError: If the request fails or the provider is not configured
        
        Example:
            >>> auth = ProjectAuthClient(project_url="myproject")
            >>> result = auth.get_oauth_authorization_url(
            ...     provider="github",
            ...     redirect_uri="http://localhost:5000/auth/github/callback"
            ... )
            >>> # Redirect user to result["authorization_url"]
            >>> # After GitHub auth, backend will redirect to redirect_uri with tokens
        """
        if not provider or not provider.strip():
            raise WowSQLError("provider is required and cannot be empty")
        
        provider = provider.strip()
        
        # Build params - use frontend_redirect_uri parameter name for clarity
        params = {}
        if redirect_uri:
            params["frontend_redirect_uri"] = redirect_uri.strip()
        
        try:
            data = self._request(
                "GET",
                f"/oauth/{provider}",
                params=params,
            )
            return {
                "authorization_url": data.get("authorization_url", ""),
                "provider": data.get("provider", provider),
                "backend_callback_url": data.get("backend_callback_url", ""),
                "frontend_redirect_uri": data.get("frontend_redirect_uri", redirect_uri or ""),
            }
        except WowSQLError as e:
            # Provide more helpful error messages
            if e.status_code == 502:
                raise WowSQLError(
                    f"Bad Gateway (502): The backend server may be down or unreachable. "
                    f"Check if the backend is running and accessible at {self.base_url}",
                    status_code=502,
                    response=getattr(e, 'response', {})
                )
            elif e.status_code == 400:
                raise WowSQLError(
                    f"Bad Request (400): {e}. "
                    f"Ensure OAuth provider '{provider}' is configured and enabled for this project.",
                    status_code=400,
                    response=getattr(e, 'response', {})
                )
            raise

    def exchange_oauth_callback(
        self,
        provider: str,
        *,
        code: str,
        redirect_uri: Optional[str] = None,
    ) -> AuthResponse:
        """
        Exchange OAuth callback code for access tokens.
        
        After the user authorizes with the OAuth provider, the provider redirects
        back with a code. Call this method to exchange that code for JWT tokens.
        
        Args:
            provider: OAuth provider name (e.g., 'github', 'google')
            code: Authorization code from OAuth provider callback
            redirect_uri: Optional redirect URI (uses configured one if not provided)
        
        Returns:
            AuthResponse with session tokens and user info
        """
        payload = {
            "code": code,
            "redirect_uri": redirect_uri,
        }
        data = self._request(
            "POST",
            f"/oauth/{provider}/callback",
            json=payload,
        )
        session = self._persist_session(data)
        user = AuthUser(**_normalize_user(data.get("user"))) if data.get("user") else None
        return AuthResponse(session=session, user=user)

    def forgot_password(self, *, email: str) -> Dict[str, Any]:
        """
        Request password reset.
        
        Sends a password reset email to the user if they exist.
        Always returns success to prevent email enumeration.
        
        Args:
            email: User's email address
        
        Returns:
            Dict with success status and message
        """
        payload = {"email": email}
        data = self._request("POST", "/forgot-password", json=payload)
        return {
            "success": data.get("success", True),
            "message": data.get("message", "If that email exists, a password reset link has been sent")
        }

    def reset_password(self, *, token: str, new_password: str) -> Dict[str, Any]:
        """
        Reset password with token.
        
        Validates the reset token and updates the user's password.
        
        Args:
            token: Password reset token from email
            new_password: New password (minimum 8 characters)
        
        Returns:
            Dict with success status and message
        """
        payload = {
            "token": token,
            "new_password": new_password
        }
        data = self._request("POST", "/reset-password", json=payload)
        return {
            "success": data.get("success", True),
            "message": data.get("message", "Password reset successfully! You can now login with your new password")
        }

    def send_otp(self, *, email: str, purpose: str = "login") -> Dict[str, Any]:
        """
        Send OTP code to user's email.
        
        Supports login, signup, and password_reset purposes.
        
        Args:
            email: User's email address
            purpose: Purpose of OTP - 'login', 'signup', or 'password_reset' (default: 'login')
        
        Returns:
            Dict with success status and message
        """
        if purpose not in ['login', 'signup', 'password_reset']:
            raise WowSQLError("Purpose must be 'login', 'signup', or 'password_reset'")
        
        payload = {
            "email": email,
            "purpose": purpose
        }
        data = self._request("POST", "/otp/send", json=payload)
        return {
            "success": data.get("success", True),
            "message": data.get("message", "If that email exists, an OTP code has been sent")
        }

    def verify_otp(
        self,
        *,
        email: str,
        otp: str,
        purpose: str = "login",
        new_password: Optional[str] = None
    ) -> AuthResponse:
        """
        Verify OTP and complete authentication.
        
        For signup: Creates new user if doesn't exist
        For login: Authenticates existing user
        For password_reset: Updates password if new_password provided
        
        Args:
            email: User's email address
            otp: 6-digit OTP code
            purpose: Purpose of OTP - 'login', 'signup', or 'password_reset' (default: 'login')
            new_password: Required for password_reset purpose, new password (minimum 8 characters)
        
        Returns:
            AuthResponse with session tokens and user info (for login/signup)
            Dict with success message (for password_reset)
        """
        if purpose not in ['login', 'signup', 'password_reset']:
            raise WowSQLError("Purpose must be 'login', 'signup', or 'password_reset'")
        
        if purpose == 'password_reset' and not new_password:
            raise WowSQLError("new_password is required for password_reset purpose")
        
        payload = {
            "email": email,
            "otp": otp,
            "purpose": purpose
        }
        if new_password:
            payload["new_password"] = new_password
        
        data = self._request("POST", "/otp/verify", json=payload)
        
        if purpose == 'password_reset':
            return {
                "success": data.get("success", True),
                "message": data.get("message", "Password reset successfully! You can now login with your new password")
            }
        
        session = self._persist_session(data)
        user = AuthUser(**_normalize_user(data.get("user"))) if data.get("user") else None
        return AuthResponse(session=session, user=user)

    def send_magic_link(self, *, email: str, purpose: str = "login") -> Dict[str, Any]:
        """
        Send magic link to user's email.
        
        Supports login, signup, and email_verification purposes.
        
        Args:
            email: User's email address
            purpose: Purpose of magic link - 'login', 'signup', or 'email_verification' (default: 'login')
        
        Returns:
            Dict with success status and message
        """
        if purpose not in ['login', 'signup', 'email_verification']:
            raise WowSQLError("Purpose must be 'login', 'signup', or 'email_verification'")
        
        payload = {
            "email": email,
            "purpose": purpose
        }
        data = self._request("POST", "/magic-link/send", json=payload)
        return {
            "success": data.get("success", True),
            "message": data.get("message", "If that email exists, a magic link has been sent")
        }

    def verify_email(self, *, token: str) -> Dict[str, Any]:
        """
        Verify email using token (from magic link or OTP verification).
        
        Marks email as verified and sends welcome email.
        
        Args:
            token: Verification token from email
        
        Returns:
            Dict with success status, message, and user info
        """
        payload = {"token": token}
        data = self._request("POST", "/verify-email", json=payload)
        return {
            "success": data.get("success", True),
            "message": data.get("message", "Email verified successfully!"),
            "user": AuthUser(**_normalize_user(data.get("user"))) if data.get("user") else None
        }

    def resend_verification(self, *, email: str) -> Dict[str, Any]:
        """
        Resend verification email.
        
        Always returns success to prevent email enumeration.
        
        Args:
            email: User's email address
        
        Returns:
            Dict with success status and message
        """
        payload = {"email": email}
        data = self._request("POST", "/resend-verification", json=payload)
        return {
            "success": data.get("success", True),
            "message": data.get("message", "If that email exists, a verification email has been sent")
        }

    def get_session(self) -> Dict[str, Optional[str]]:
        return {
            "access_token": self._access_token or self.storage.get_access_token(),
            "refresh_token": self._refresh_token or self.storage.get_refresh_token(),
        }

    def set_session(self, *, access_token: str, refresh_token: Optional[str] = None) -> None:
        self._access_token = access_token
        self._refresh_token = refresh_token
        self.storage.set_access_token(access_token)
        self.storage.set_refresh_token(refresh_token)

    def clear_session(self) -> None:
        self._access_token = None
        self._refresh_token = None
        self.storage.set_access_token(None)
        self.storage.set_refresh_token(None)

    def close(self) -> None:
        self.session.close()

    # ------------------------- Internals ---------------------------- #

    def _persist_session(self, data: Dict[str, Any]) -> AuthSession:
        session = AuthSession(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            token_type=data.get("token_type", "bearer"),
            expires_in=data.get("expires_in", 0),
        )
        self._access_token = session.access_token
        self._refresh_token = session.refresh_token
        self.storage.set_access_token(session.access_token)
        self.storage.set_refresh_token(session.refresh_token)
        return session

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        request_headers = dict(headers or {})

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=json,
                params=params,
                headers=request_headers,
                timeout=self.timeout,
            )
        except requests.exceptions.SSLError as exc:
            raise WowSQLError(
                f"SSL error: {str(exc)}. If using self-signed certificates, set verify_ssl=False",
                response={"error": str(exc)}
            )
        except requests.exceptions.ConnectionError as exc:
            raise WowSQLError(
                f"Connection error: {str(exc)}. Check if the backend is running and the URL is correct.",
                response={"error": str(exc)}
            )
        except requests.exceptions.Timeout as exc:
            raise WowSQLError(
                f"Request timeout: {str(exc)}. The server took too long to respond.",
                response={"error": str(exc)}
            )
        except requests.exceptions.RequestException as exc:
            raise WowSQLError(
                f"Request failed: {str(exc)}",
                response={"error": str(exc)}
            )

        if response.status_code >= 400:
            try:
                payload = response.json()
            except ValueError:
                payload = {}
            message = (
                payload.get("detail")
                or payload.get("message")
                or payload.get("error")
                or f"Request failed with status {response.status_code}"
            )
            raise WowSQLError(message, status_code=response.status_code, response=payload)

        if not response.content:
            return {}
        try:
            return response.json()
        except ValueError as exc:
            raise WowSQLError(f"Failed to parse response: {exc}") from exc


def _build_auth_base_url(project_url: str, base_domain: str, secure: bool) -> str:
    normalized = project_url.strip()
    
    # If it's already a full URL, use it as-is
    if normalized.startswith("http://") or normalized.startswith("https://"):
        # Already a full URL, just normalize
        normalized = normalized.rstrip("/")
        if normalized.endswith("/api"):
            normalized = normalized[: -len("/api")]
        return f"{normalized}/api/auth"
    
    # If it already contains the base domain, don't append it again
    if f".{base_domain}" in normalized or normalized.endswith(base_domain):
        protocol = "https" if secure else "http"
        normalized = f"{protocol}://{normalized}"
    else:
        # Just a project slug, append domain
        protocol = "https" if secure else "http"
        normalized = f"{protocol}://{normalized}.{base_domain}"
    
    normalized = normalized.rstrip("/")
    if normalized.endswith("/api"):
        normalized = normalized[: -len("/api")]
    
    return f"{normalized}/api/auth"


def _normalize_user(user: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": user.get("id"),
        "email": user.get("email"),
        "full_name": user.get("full_name") or user.get("fullName"),
        "avatar_url": user.get("avatar_url") or user.get("avatarUrl"),
        "email_verified": bool(user.get("email_verified") or user.get("emailVerified")),
        "user_metadata": user.get("user_metadata") or user.get("userMetadata") or {},
        "app_metadata": user.get("app_metadata") or user.get("appMetadata") or {},
        "created_at": user.get("created_at") or user.get("createdAt"),
    }

