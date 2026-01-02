"""
Portal Namespace - User authentication and session orchestration.

Provides login, logout, session management, profile, and navigation access.
"""
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..start import Dominus


class PortalNamespace:
    """
    User authentication and session namespace.

    All portal operations go through /api/portal/* endpoints.
    Orchestrates Guardian (user data) + Warden (JWT minting).

    Usage:
        # User login
        session = await dominus.portal.login(
            username="john@example.com",
            password="secret123",
            tenant_id="tenant-uuid"
        )

        # Get current user
        me = await dominus.portal.me()

        # Switch tenant
        await dominus.portal.switch_tenant("other-tenant-uuid")

        # Get navigation
        nav = await dominus.portal.get_navigation()
    """

    def __init__(self, client: "Dominus"):
        self._client = client

    # ========================================
    # AUTHENTICATION
    # ========================================

    async def login(
        self,
        username: str,
        password: str,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Login user with password.

        Args:
            username: Username or email
            password: User password
            tenant_id: Optional tenant UUID/slug. If not provided, uses user's first available tenant.

        Returns:
            Dict with user info, active tenant, available tenants list, and session_id
        """
        body: Dict[str, str] = {
            "username": username,
            "password": password
        }
        if tenant_id:
            body["tenant_id"] = tenant_id

        return await self._client._request(
            endpoint="/api/portal/auth/login",
            body=body
        )

    async def login_client(
        self,
        psk: str,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Login service client with PSK.

        Client is looked up by PSK directly - no client_id needed.

        Args:
            psk: Pre-shared key
            tenant_id: Optional tenant UUID. If not provided, uses client's first assigned tenant.

        Returns:
            Dict with access_token, token_type, expires_in, session_id
        """
        body: Dict[str, str] = {"psk": psk}
        if tenant_id:
            body["tenant_id"] = tenant_id
        return await self._client._request(
            endpoint="/api/portal/auth/login-client",
            body=body
        )

    async def logout(self, user_token: Optional[str] = None) -> Dict[str, Any]:
        """
        End session and clear cookie.

        Args:
            user_token: Optional user JWT for user-authenticated requests
        """
        return await self._client._request(
            endpoint="/api/portal/auth/logout",
            body={},
            user_token=user_token
        )

    async def refresh(self, user_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Refresh JWT token using existing session.

        Args:
            user_token: Optional user JWT for user-authenticated requests
        """
        return await self._client._request(
            endpoint="/api/portal/auth/refresh",
            body={},
            user_token=user_token
        )

    async def me(self, user_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current user/client info.

        Args:
            user_token: Optional user JWT for user-authenticated requests

        Returns:
            Dict with subject_type, user/client info, tenants, scopes, roles
        """
        return await self._client._request(
            endpoint="/api/portal/auth/me",
            method="GET",
            user_token=user_token
        )

    async def switch_tenant(self, tenant_id: str, user_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Switch active tenant context.

        Args:
            tenant_id: Tenant UUID to switch to
            user_token: Optional user JWT for user-authenticated requests

        Returns:
            Dict with success status and new tenant info
        """
        return await self._client._request(
            endpoint="/api/portal/auth/switch-tenant",
            body={"tenant_id": tenant_id},
            user_token=user_token
        )

    # ========================================
    # SECURITY
    # ========================================

    async def change_password(
        self,
        current_password: str,
        new_password: str,
        user_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Change current user's password.

        Args:
            current_password: Current password for verification
            new_password: New password to set
            user_token: Optional user JWT for user-authenticated requests

        Returns:
            Dict with success status
        """
        return await self._client._request(
            endpoint="/api/portal/security/change-password",
            body={
                "current_password": current_password,
                "new_password": new_password
            },
            user_token=user_token
        )

    async def request_password_reset(self, email: str) -> Dict[str, Any]:
        """
        Request password reset email.

        Args:
            email: User's email address

        Returns:
            Dict with success status (always true for security)
        """
        return await self._client._request(
            endpoint="/api/portal/security/request-reset",
            body={"email": email}
        )

    async def confirm_password_reset(
        self,
        token: str,
        new_password: str
    ) -> Dict[str, Any]:
        """
        Confirm password reset with token.

        Args:
            token: Reset token from email
            new_password: New password to set

        Returns:
            Dict with success status
        """
        return await self._client._request(
            endpoint="/api/portal/security/confirm-reset",
            body={"token": token, "new_password": new_password}
        )

    async def list_sessions(self, user_token: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all active sessions for current user.

        Args:
            user_token: Optional user JWT for user-authenticated requests
        """
        return await self._client._request(
            endpoint="/api/portal/security/sessions",
            method="GET",
            user_token=user_token
        )

    async def revoke_session(self, session_id: str, user_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Revoke a specific session.

        Args:
            session_id: Session ID to revoke
            user_token: Optional user JWT for user-authenticated requests
        """
        return await self._client._request(
            endpoint=f"/api/portal/security/sessions/{session_id}",
            method="DELETE",
            user_token=user_token
        )

    async def revoke_all_sessions(self, user_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Revoke all sessions except current.

        Args:
            user_token: Optional user JWT for user-authenticated requests
        """
        return await self._client._request(
            endpoint="/api/portal/security/sessions/revoke-all",
            body={},
            user_token=user_token
        )

    # ========================================
    # PROFILE
    # ========================================

    async def get_profile(self, user_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current user's profile.

        Args:
            user_token: Optional user JWT for user-authenticated requests
        """
        return await self._client._request(
            endpoint="/api/portal/profile",
            method="GET",
            user_token=user_token
        )

    async def update_profile(
        self,
        display_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        bio: Optional[str] = None,
        phone: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
        user_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update user profile.

        Args:
            display_name: Display name
            avatar_url: Avatar image URL
            bio: User biography
            phone: Phone number
            extra: Additional metadata (JSONB)
            user_token: Optional user JWT for user-authenticated requests

        Returns:
            Updated profile
        """
        body = {}
        if display_name is not None:
            body["display_name"] = display_name
        if avatar_url is not None:
            body["avatar_url"] = avatar_url
        if bio is not None:
            body["bio"] = bio
        if phone is not None:
            body["phone"] = phone
        if extra is not None:
            body["extra"] = extra

        return await self._client._request(
            endpoint="/api/portal/profile",
            method="PUT",
            body=body,
            user_token=user_token
        )

    async def get_preferences(self, user_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current user's preferences.

        Args:
            user_token: Optional user JWT for user-authenticated requests
        """
        return await self._client._request(
            endpoint="/api/portal/profile/preferences",
            method="GET",
            user_token=user_token
        )

    async def update_preferences(
        self,
        theme: Optional[str] = None,
        language: Optional[str] = None,
        timezone: Optional[str] = None,
        sidebar_collapsed: Optional[bool] = None,
        notifications_enabled: Optional[bool] = None,
        email_notifications: Optional[bool] = None,
        extra: Optional[Dict[str, Any]] = None,
        user_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update user preferences.

        Args:
            theme: UI theme (light/dark/system)
            language: Preferred language code
            timezone: Timezone (e.g., "America/New_York")
            sidebar_collapsed: Sidebar state
            notifications_enabled: Push notifications
            email_notifications: Email notifications
            extra: Additional preferences (JSONB)
            user_token: Optional user JWT for user-authenticated requests

        Returns:
            Updated preferences
        """
        body = {}
        if theme is not None:
            body["theme"] = theme
        if language is not None:
            body["language"] = language
        if timezone is not None:
            body["timezone"] = timezone
        if sidebar_collapsed is not None:
            body["sidebar_collapsed"] = sidebar_collapsed
        if notifications_enabled is not None:
            body["notifications_enabled"] = notifications_enabled
        if email_notifications is not None:
            body["email_notifications"] = email_notifications
        if extra is not None:
            body["extra"] = extra

        return await self._client._request(
            endpoint="/api/portal/profile/preferences",
            method="PUT",
            body=body,
            user_token=user_token
        )

    # ========================================
    # NAVIGATION
    # ========================================

    async def get_navigation(self, user_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Get navigation tree for current user's tenant.

        Args:
            user_token: Optional user JWT for user-authenticated requests

        Returns:
            Hierarchical nav structure with access-filtered items.
        """
        return await self._client._request(
            endpoint="/api/portal/nav/tree",
            method="GET",
            user_token=user_token
        )

    async def check_page_access(self, path: str, user_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Check if current user can access a page.

        Args:
            path: Page path to check
            user_token: Optional user JWT for user-authenticated requests

        Returns:
            Dict with allowed (bool) and reason
        """
        return await self._client._request(
            endpoint="/api/portal/nav/check-access",
            body={"path": path},
            user_token=user_token
        )

    # ========================================
    # REGISTRATION
    # ========================================

    async def register(
        self,
        username: str,
        email: str,
        password: str,
        tenant_id: str
    ) -> Dict[str, Any]:
        """
        Self-register new user.

        Requires tenant to allow public registration.

        Args:
            username: Desired username
            email: Email address
            password: Password
            tenant_id: Tenant to register with

        Returns:
            Dict with user info and verification status
        """
        return await self._client._request(
            endpoint="/api/portal/register",
            body={
                "username": username,
                "email": email,
                "password": password,
                "tenant_id": tenant_id
            }
        )

    async def verify_email(self, token: str) -> Dict[str, Any]:
        """
        Verify email with token.

        Args:
            token: Verification token from email

        Returns:
            Dict with success status
        """
        return await self._client._request(
            endpoint="/api/portal/register/verify",
            body={"token": token}
        )

    async def resend_verification(self, email: str) -> Dict[str, Any]:
        """
        Resend verification email.

        Args:
            email: User's email address

        Returns:
            Dict with success status
        """
        return await self._client._request(
            endpoint="/api/portal/register/resend-verification",
            body={"email": email}
        )

    async def accept_invitation(
        self,
        token: str,
        password: str
    ) -> Dict[str, Any]:
        """
        Accept admin invitation and set password.

        Args:
            token: Invitation token from email
            password: Password to set

        Returns:
            Dict with user info and login token
        """
        return await self._client._request(
            endpoint="/api/portal/register/accept-invitation",
            body={"token": token, "password": password}
        )
