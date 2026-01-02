"""
Auth Namespace - Guardian authentication and authorization operations.

Provides management of users, roles, scopes, tenants, clients, pages, and navigation.
Uses RESTful patterns matching the Guardian backend.
"""
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..start import Dominus


class AuthNamespace:
    """
    Authentication and authorization namespace.

    All auth operations go through /api/guardian/* endpoints.
    Uses RESTful patterns: GET/POST/PUT/DELETE with path params.

    Usage:
        # User management
        user = await dominus.auth.create_user(username="john", email="j@ex.com", password="secret")
        users = await dominus.auth.list_users(status="active")
        await dominus.auth.update_password(user_id, "new_password")

        # Role management
        role = await dominus.auth.create_role(name="admin", description="Admin role")
        roles = await dominus.auth.list_roles()

        # JWT validation
        claims = await dominus.auth.validate_jwt(token)
    """

    def __init__(self, client: "Dominus"):
        self._client = client
        self._public_key_cache = None

    # ========================================
    # USERS
    # ========================================

    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        status: str = "active"
    ) -> Dict[str, Any]:
        """
        Create a new user.

        Args:
            username: Unique username
            email: Email address
            password: Raw password (will be hashed server-side)
            status: User status (default: "active")

        Returns:
            Created user record (without password_hash)
        """
        return await self._client._request(
            endpoint="/api/guardian/users",
            body={
                "username": username,
                "email": email,
                "password": password,
                "status": status
            }
        )

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user by ID."""
        return await self._client._request(
            endpoint=f"/api/guardian/users/{user_id}",
            method="GET"
        )

    async def list_users(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "created_at",
        order_desc: bool = True
    ) -> Dict[str, Any]:
        """
        List users with optional filters.

        Returns:
            Dict with "items" list and "total" count
        """
        params = f"?limit={limit}&offset={offset}&order_by={order_by}&order_desc={str(order_desc).lower()}"
        if status:
            params += f"&status={status}"

        return await self._client._request(
            endpoint=f"/api/guardian/users{params}",
            method="GET"
        )

    async def update_user(
        self,
        user_id: str,
        username: Optional[str] = None,
        email: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update user fields."""
        body = {}
        if username is not None:
            body["username"] = username
        if email is not None:
            body["email"] = email
        if status is not None:
            body["status"] = status

        return await self._client._request(
            endpoint=f"/api/guardian/users/{user_id}",
            method="PUT",
            body=body
        )

    async def delete_user(self, user_id: str) -> Dict[str, Any]:
        """Delete a user."""
        return await self._client._request(
            endpoint=f"/api/guardian/users/{user_id}",
            method="DELETE"
        )

    async def update_password(self, user_id: str, password: str) -> Dict[str, Any]:
        """Update user password."""
        return await self._client._request(
            endpoint=f"/api/guardian/users/{user_id}/password",
            method="PUT",
            body={"password": password}
        )

    async def verify_password(self, user_id: str, password: str) -> Dict[str, Any]:
        """Verify user password."""
        return await self._client._request(
            endpoint=f"/api/guardian/users/{user_id}/verify-password",
            body={"password": password}
        )

    # User junction tables
    async def get_user_roles(self, user_id: str) -> List[Dict[str, Any]]:
        """Get roles assigned to user."""
        return await self._client._request(
            endpoint=f"/api/guardian/users/{user_id}/roles",
            method="GET"
        )

    async def add_user_roles(self, user_id: str, role_ids: List[str]) -> Dict[str, Any]:
        """Add roles to user."""
        return await self._client._request(
            endpoint=f"/api/guardian/users/{user_id}/roles",
            body={"role_ids": role_ids}
        )

    async def remove_user_roles(self, user_id: str, role_ids: List[str]) -> Dict[str, Any]:
        """Remove roles from user."""
        return await self._client._request(
            endpoint=f"/api/guardian/users/{user_id}/roles",
            method="DELETE",
            body={"role_ids": role_ids}
        )

    async def get_user_scopes(self, user_id: str) -> List[Dict[str, Any]]:
        """Get scopes assigned to user."""
        return await self._client._request(
            endpoint=f"/api/guardian/users/{user_id}/scopes",
            method="GET"
        )

    async def add_user_scopes(self, user_id: str, scope_ids: List[str]) -> Dict[str, Any]:
        """Add scopes to user."""
        return await self._client._request(
            endpoint=f"/api/guardian/users/{user_id}/scopes",
            body={"scope_ids": scope_ids}
        )

    async def remove_user_scopes(self, user_id: str, scope_ids: List[str]) -> Dict[str, Any]:
        """Remove scopes from user."""
        return await self._client._request(
            endpoint=f"/api/guardian/users/{user_id}/scopes",
            method="DELETE",
            body={"scope_ids": scope_ids}
        )

    async def get_user_tenants(self, user_id: str) -> List[Dict[str, Any]]:
        """Get tenants assigned to user."""
        return await self._client._request(
            endpoint=f"/api/guardian/users/{user_id}/tenants",
            method="GET"
        )

    async def add_user_tenants(self, user_id: str, tenant_ids: List[str]) -> Dict[str, Any]:
        """Add tenants to user."""
        return await self._client._request(
            endpoint=f"/api/guardian/users/{user_id}/tenants",
            body={"tenant_ids": tenant_ids}
        )

    async def remove_user_tenants(self, user_id: str, tenant_ids: List[str]) -> Dict[str, Any]:
        """Remove tenants from user."""
        return await self._client._request(
            endpoint=f"/api/guardian/users/{user_id}/tenants",
            method="DELETE",
            body={"tenant_ids": tenant_ids}
        )

    async def get_user_subtypes(self, user_id: str) -> List[Dict[str, Any]]:
        """Get subtypes assigned to user."""
        return await self._client._request(
            endpoint=f"/api/guardian/users/{user_id}/subtypes",
            method="GET"
        )

    async def add_user_subtypes(self, user_id: str, subtype_ids: List[str]) -> Dict[str, Any]:
        """Add subtypes to user."""
        return await self._client._request(
            endpoint=f"/api/guardian/users/{user_id}/subtypes",
            body={"subtype_ids": subtype_ids}
        )

    async def remove_user_subtypes(self, user_id: str, subtype_ids: List[str]) -> Dict[str, Any]:
        """Remove subtypes from user."""
        return await self._client._request(
            endpoint=f"/api/guardian/users/{user_id}/subtypes",
            method="DELETE",
            body={"subtype_ids": subtype_ids}
        )

    # ========================================
    # ROLES
    # ========================================

    async def create_role(
        self,
        name: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new role."""
        body = {"name": name}
        if description:
            body["description"] = description

        return await self._client._request(
            endpoint="/api/guardian/roles",
            body=body
        )

    async def get_role(self, role_id: str) -> Dict[str, Any]:
        """Get role by ID."""
        return await self._client._request(
            endpoint=f"/api/guardian/roles/{role_id}",
            method="GET"
        )

    async def list_roles(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List all roles."""
        return await self._client._request(
            endpoint=f"/api/guardian/roles?limit={limit}&offset={offset}",
            method="GET"
        )

    async def update_role(
        self,
        role_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update role."""
        body = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description

        return await self._client._request(
            endpoint=f"/api/guardian/roles/{role_id}",
            method="PUT",
            body=body
        )

    async def delete_role(self, role_id: str) -> Dict[str, Any]:
        """Delete a role."""
        return await self._client._request(
            endpoint=f"/api/guardian/roles/{role_id}",
            method="DELETE"
        )

    async def get_role_scopes(self, role_id: str) -> List[Dict[str, Any]]:
        """Get scopes assigned to role."""
        return await self._client._request(
            endpoint=f"/api/guardian/roles/{role_id}/scopes",
            method="GET"
        )

    async def add_role_scopes(self, role_id: str, scope_ids: List[str]) -> Dict[str, Any]:
        """Add scopes to role."""
        return await self._client._request(
            endpoint=f"/api/guardian/roles/{role_id}/scopes",
            body={"scope_ids": scope_ids}
        )

    async def remove_role_scopes(self, role_id: str, scope_ids: List[str]) -> Dict[str, Any]:
        """Remove scopes from role."""
        return await self._client._request(
            endpoint=f"/api/guardian/roles/{role_id}/scopes",
            method="DELETE",
            body={"scope_ids": scope_ids}
        )

    # ========================================
    # SCOPES
    # ========================================

    async def create_scope(
        self,
        slug: str,
        display_name: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new scope."""
        body = {"slug": slug, "display_name": display_name}
        if description:
            body["description"] = description

        return await self._client._request(
            endpoint="/api/guardian/scopes",
            body=body
        )

    async def get_scope(self, scope_id: str) -> Dict[str, Any]:
        """Get scope by ID."""
        return await self._client._request(
            endpoint=f"/api/guardian/scopes/{scope_id}",
            method="GET"
        )

    async def list_scopes(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List all scopes."""
        return await self._client._request(
            endpoint=f"/api/guardian/scopes?limit={limit}&offset={offset}",
            method="GET"
        )

    async def update_scope(
        self,
        scope_id: str,
        slug: Optional[str] = None,
        display_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update scope."""
        body = {}
        if slug is not None:
            body["slug"] = slug
        if display_name is not None:
            body["display_name"] = display_name
        if description is not None:
            body["description"] = description

        return await self._client._request(
            endpoint=f"/api/guardian/scopes/{scope_id}",
            method="PUT",
            body=body
        )

    async def delete_scope(self, scope_id: str) -> Dict[str, Any]:
        """Delete a scope."""
        return await self._client._request(
            endpoint=f"/api/guardian/scopes/{scope_id}",
            method="DELETE"
        )

    # ========================================
    # CLIENTS (PSK/Machine Auth)
    # ========================================

    async def create_client(
        self,
        label: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new service client with PSK.

        Returns dict with client info and one-time-visible "psk".
        """
        body = {"label": label}
        if description:
            body["description"] = description

        return await self._client._request(
            endpoint="/api/guardian/clients",
            body=body
        )

    async def get_client(self, client_id: str) -> Dict[str, Any]:
        """Get client by ID."""
        return await self._client._request(
            endpoint=f"/api/guardian/clients/{client_id}",
            method="GET"
        )

    async def list_clients(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List all clients."""
        return await self._client._request(
            endpoint=f"/api/guardian/clients?limit={limit}&offset={offset}",
            method="GET"
        )

    async def update_client(
        self,
        client_id: str,
        label: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update client."""
        body = {}
        if label is not None:
            body["label"] = label
        if description is not None:
            body["description"] = description
        if status is not None:
            body["status"] = status

        return await self._client._request(
            endpoint=f"/api/guardian/clients/{client_id}",
            method="PUT",
            body=body
        )

    async def delete_client(self, client_id: str) -> Dict[str, Any]:
        """Delete a client."""
        return await self._client._request(
            endpoint=f"/api/guardian/clients/{client_id}",
            method="DELETE"
        )

    async def regenerate_psk(self, client_id: str) -> Dict[str, Any]:
        """Regenerate client PSK. Returns new one-time-visible PSK."""
        return await self._client._request(
            endpoint=f"/api/guardian/clients/{client_id}/regenerate-psk",
            body={}
        )

    async def verify_psk(self, client_id: str, psk: str) -> Dict[str, Any]:
        """Verify client PSK."""
        return await self._client._request(
            endpoint=f"/api/guardian/clients/{client_id}/verify-psk",
            body={"psk": psk}
        )

    # Client junction tables
    async def get_client_tenants(self, client_id: str) -> List[Dict[str, Any]]:
        """Get tenants assigned to client."""
        return await self._client._request(
            endpoint=f"/api/guardian/clients/{client_id}/tenants",
            method="GET"
        )

    async def add_client_tenants(self, client_id: str, tenant_ids: List[str]) -> Dict[str, Any]:
        """Add tenants to client."""
        return await self._client._request(
            endpoint=f"/api/guardian/clients/{client_id}/tenants",
            body={"tenant_ids": tenant_ids}
        )

    async def remove_client_tenants(self, client_id: str, tenant_ids: List[str]) -> Dict[str, Any]:
        """Remove tenants from client."""
        return await self._client._request(
            endpoint=f"/api/guardian/clients/{client_id}/tenants",
            method="DELETE",
            body={"tenant_ids": tenant_ids}
        )

    # ========================================
    # TENANTS
    # ========================================

    async def create_tenant(
        self,
        name: str,
        slug: str,
        category_id: Optional[str] = None,
        display_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new tenant."""
        body = {"name": name, "slug": slug}
        if category_id:
            body["category_id"] = category_id
        if display_name:
            body["display_name"] = display_name
        if description:
            body["description"] = description

        return await self._client._request(
            endpoint="/api/guardian/tenants",
            body=body
        )

    async def get_tenant(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant by ID."""
        return await self._client._request(
            endpoint=f"/api/guardian/tenants/{tenant_id}",
            method="GET"
        )

    async def list_tenants(
        self,
        status: Optional[str] = None,
        category_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List tenants with optional filters."""
        params = f"?limit={limit}&offset={offset}"
        if status:
            params += f"&status={status}"
        if category_id:
            params += f"&category_id={category_id}"

        return await self._client._request(
            endpoint=f"/api/guardian/tenants{params}",
            method="GET"
        )

    async def update_tenant(
        self,
        tenant_id: str,
        name: Optional[str] = None,
        display_name: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update tenant."""
        body = {}
        if name is not None:
            body["name"] = name
        if display_name is not None:
            body["display_name"] = display_name
        if status is not None:
            body["status"] = status

        return await self._client._request(
            endpoint=f"/api/guardian/tenants/{tenant_id}",
            method="PUT",
            body=body
        )

    async def delete_tenant(self, tenant_id: str) -> Dict[str, Any]:
        """Delete a tenant."""
        return await self._client._request(
            endpoint=f"/api/guardian/tenants/{tenant_id}",
            method="DELETE"
        )

    # ========================================
    # TENANT CATEGORIES
    # ========================================

    async def create_tenant_category(
        self,
        name: str,
        slug: str,
        description: Optional[str] = None,
        color: str = "#3B82F6"
    ) -> Dict[str, Any]:
        """Create a new tenant category."""
        body = {"name": name, "slug": slug, "color": color}
        if description:
            body["description"] = description

        return await self._client._request(
            endpoint="/api/guardian/tenant-categories",
            body=body
        )

    async def get_tenant_category(self, category_id: str) -> Dict[str, Any]:
        """Get tenant category by ID."""
        return await self._client._request(
            endpoint=f"/api/guardian/tenant-categories/{category_id}",
            method="GET"
        )

    async def list_tenant_categories(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List all tenant categories."""
        return await self._client._request(
            endpoint=f"/api/guardian/tenant-categories?limit={limit}&offset={offset}",
            method="GET"
        )

    async def update_tenant_category(
        self,
        category_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update tenant category."""
        body = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if color is not None:
            body["color"] = color

        return await self._client._request(
            endpoint=f"/api/guardian/tenant-categories/{category_id}",
            method="PUT",
            body=body
        )

    async def delete_tenant_category(self, category_id: str) -> Dict[str, Any]:
        """Delete a tenant category."""
        return await self._client._request(
            endpoint=f"/api/guardian/tenant-categories/{category_id}",
            method="DELETE"
        )

    # ========================================
    # SUBTYPES
    # ========================================

    async def create_subtype(
        self,
        name: str,
        slug: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new user subtype."""
        body = {"name": name, "slug": slug}
        if description:
            body["description"] = description

        return await self._client._request(
            endpoint="/api/guardian/subtypes",
            body=body
        )

    async def get_subtype(self, subtype_id: str) -> Dict[str, Any]:
        """Get subtype by ID."""
        return await self._client._request(
            endpoint=f"/api/guardian/subtypes/{subtype_id}",
            method="GET"
        )

    async def list_subtypes(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List all subtypes."""
        return await self._client._request(
            endpoint=f"/api/guardian/subtypes?limit={limit}&offset={offset}",
            method="GET"
        )

    async def update_subtype(
        self,
        subtype_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update subtype."""
        body = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description

        return await self._client._request(
            endpoint=f"/api/guardian/subtypes/{subtype_id}",
            method="PUT",
            body=body
        )

    async def delete_subtype(self, subtype_id: str) -> Dict[str, Any]:
        """Delete a subtype."""
        return await self._client._request(
            endpoint=f"/api/guardian/subtypes/{subtype_id}",
            method="DELETE"
        )

    # ========================================
    # PAGES
    # ========================================

    async def create_page(
        self,
        path: str,
        name: str,
        description: Optional[str] = None,
        is_active: bool = True
    ) -> Dict[str, Any]:
        """Create a new page."""
        body = {"path": path, "name": name, "is_active": is_active}
        if description:
            body["description"] = description

        return await self._client._request(
            endpoint="/api/guardian/pages",
            body=body
        )

    async def get_page(self, page_id: str) -> Dict[str, Any]:
        """Get page by ID."""
        return await self._client._request(
            endpoint=f"/api/guardian/pages/{page_id}",
            method="GET"
        )

    async def list_pages(
        self,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List pages with optional filters."""
        params = f"?limit={limit}&offset={offset}"
        if is_active is not None:
            params += f"&is_active={str(is_active).lower()}"

        return await self._client._request(
            endpoint=f"/api/guardian/pages{params}",
            method="GET"
        )

    async def update_page(
        self,
        page_id: str,
        path: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Update page."""
        body = {}
        if path is not None:
            body["path"] = path
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if is_active is not None:
            body["is_active"] = is_active

        return await self._client._request(
            endpoint=f"/api/guardian/pages/{page_id}",
            method="PUT",
            body=body
        )

    async def delete_page(self, page_id: str) -> Dict[str, Any]:
        """Delete a page."""
        return await self._client._request(
            endpoint=f"/api/guardian/pages/{page_id}",
            method="DELETE"
        )

    # Page-tenant junction
    async def get_page_tenants(self, page_id: str) -> List[Dict[str, Any]]:
        """Get tenants assigned to page."""
        return await self._client._request(
            endpoint=f"/api/guardian/pages/{page_id}/tenants",
            method="GET"
        )

    async def add_page_tenants(self, page_id: str, tenant_ids: List[str]) -> Dict[str, Any]:
        """Add tenants to page."""
        return await self._client._request(
            endpoint=f"/api/guardian/pages/{page_id}/tenants",
            body={"tenant_ids": tenant_ids}
        )

    async def remove_page_tenants(self, page_id: str, tenant_ids: List[str]) -> Dict[str, Any]:
        """Remove tenants from page."""
        return await self._client._request(
            endpoint=f"/api/guardian/pages/{page_id}/tenants",
            method="DELETE",
            body={"tenant_ids": tenant_ids}
        )

    # Page-scope junction
    async def get_page_scopes(self, page_id: str) -> List[Dict[str, Any]]:
        """Get scopes assigned to page."""
        return await self._client._request(
            endpoint=f"/api/guardian/pages/{page_id}/scopes",
            method="GET"
        )

    async def add_page_scopes(self, page_id: str, scope_ids: List[str]) -> Dict[str, Any]:
        """Add scopes to page."""
        return await self._client._request(
            endpoint=f"/api/guardian/pages/{page_id}/scopes",
            body={"scope_ids": scope_ids}
        )

    async def remove_page_scopes(self, page_id: str, scope_ids: List[str]) -> Dict[str, Any]:
        """Remove scopes from page."""
        return await self._client._request(
            endpoint=f"/api/guardian/pages/{page_id}/scopes",
            method="DELETE",
            body={"scope_ids": scope_ids}
        )

    async def set_page_scopes(self, page_id: str, scope_ids: List[str]) -> List[Dict[str, Any]]:
        """Set all scopes for page (replaces existing)."""
        return await self._client._request(
            endpoint=f"/api/guardian/pages/{page_id}/scopes",
            method="PUT",
            body={"scope_ids": scope_ids}
        )

    # ========================================
    # NAVIGATION
    # ========================================

    async def create_nav_item(
        self,
        title: str,
        icon: Optional[str] = None,
        page_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        sort_order: int = 0
    ) -> Dict[str, Any]:
        """Create a new navigation item."""
        body = {"title": title, "sort_order": sort_order}
        if icon:
            body["icon"] = icon
        if page_id:
            body["page_id"] = page_id
        if parent_id:
            body["parent_id"] = parent_id

        return await self._client._request(
            endpoint="/api/guardian/nav-items",
            body=body
        )

    async def get_nav_item(self, nav_id: str) -> Dict[str, Any]:
        """Get navigation item by ID."""
        return await self._client._request(
            endpoint=f"/api/guardian/nav-items/{nav_id}",
            method="GET"
        )

    async def list_nav_items(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List all navigation items."""
        return await self._client._request(
            endpoint=f"/api/guardian/nav-items?limit={limit}&offset={offset}",
            method="GET"
        )

    async def update_nav_item(
        self,
        nav_id: str,
        title: Optional[str] = None,
        icon: Optional[str] = None,
        sort_order: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update navigation item."""
        body = {}
        if title is not None:
            body["title"] = title
        if icon is not None:
            body["icon"] = icon
        if sort_order is not None:
            body["sort_order"] = sort_order

        return await self._client._request(
            endpoint=f"/api/guardian/nav-items/{nav_id}",
            method="PUT",
            body=body
        )

    async def delete_nav_item(self, nav_id: str) -> Dict[str, Any]:
        """Delete a navigation item."""
        return await self._client._request(
            endpoint=f"/api/guardian/nav-items/{nav_id}",
            method="DELETE"
        )

    # Nav-tenant junction
    async def get_nav_tenants(self, nav_id: str) -> List[Dict[str, Any]]:
        """Get tenants assigned to nav item."""
        return await self._client._request(
            endpoint=f"/api/guardian/nav-items/{nav_id}/tenants",
            method="GET"
        )

    async def add_nav_tenants(self, nav_id: str, tenant_ids: List[str]) -> Dict[str, Any]:
        """Add tenants to nav item."""
        return await self._client._request(
            endpoint=f"/api/guardian/nav-items/{nav_id}/tenants",
            body={"tenant_ids": tenant_ids}
        )

    async def remove_nav_tenants(self, nav_id: str, tenant_ids: List[str]) -> Dict[str, Any]:
        """Remove tenants from nav item."""
        return await self._client._request(
            endpoint=f"/api/guardian/nav-items/{nav_id}/tenants",
            method="DELETE",
            body={"tenant_ids": tenant_ids}
        )

    # ========================================
    # SECURE TABLES
    # ========================================

    async def create_secure_table(
        self,
        table_name: str,
        schema_name: str = "public"
    ) -> Dict[str, Any]:
        """Mark a table as requiring access justification."""
        return await self._client._request(
            endpoint="/api/guardian/secure-tables",
            body={"table_name": table_name, "schema_name": schema_name}
        )

    async def get_secure_table(self, secure_table_id: str) -> Dict[str, Any]:
        """Get secure table by ID."""
        return await self._client._request(
            endpoint=f"/api/guardian/secure-tables/{secure_table_id}",
            method="GET"
        )

    async def list_secure_tables(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List all secure tables."""
        return await self._client._request(
            endpoint=f"/api/guardian/secure-tables?limit={limit}&offset={offset}",
            method="GET"
        )

    async def delete_secure_table(self, secure_table_id: str) -> Dict[str, Any]:
        """Remove secure table designation."""
        return await self._client._request(
            endpoint=f"/api/guardian/secure-tables/{secure_table_id}",
            method="DELETE"
        )

    # Secure table scope junction
    async def get_secure_table_scopes(self, secure_table_id: str) -> List[Dict[str, Any]]:
        """Get scopes required to access secure table."""
        return await self._client._request(
            endpoint=f"/api/guardian/secure-tables/{secure_table_id}/scopes",
            method="GET"
        )

    async def add_secure_table_scopes(
        self,
        secure_table_id: str,
        scope_ids: List[str]
    ) -> Dict[str, Any]:
        """Add scope requirements to secure table."""
        return await self._client._request(
            endpoint=f"/api/guardian/secure-tables/{secure_table_id}/scopes",
            body={"scope_ids": scope_ids}
        )

    async def remove_secure_table_scopes(
        self,
        secure_table_id: str,
        scope_ids: List[str]
    ) -> Dict[str, Any]:
        """Remove scope requirements from secure table."""
        return await self._client._request(
            endpoint=f"/api/guardian/secure-tables/{secure_table_id}/scopes",
            method="DELETE",
            body={"scope_ids": scope_ids}
        )

    # ========================================
    # JWT OPERATIONS (via Warden)
    # ========================================

    async def get_jwks(self) -> Dict[str, Any]:
        """Get JWKS for JWT validation (cached)."""
        if self._public_key_cache:
            return self._public_key_cache

        result = await self._client._request(
            endpoint="/api/warden/jwks",
            method="GET"
        )
        self._public_key_cache = result
        return result

    async def validate_jwt(self, token: str) -> Dict[str, Any]:
        """
        Validate a JWT and return its claims.

        Raises ValueError if token is invalid or expired.
        """
        import jwt as pyjwt
        from jwt import PyJWK

        jwks = await self.get_jwks()

        try:
            unverified_header = pyjwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            key_data = None
            for key in jwks.get("keys", []):
                if key.get("kid") == kid or kid is None:
                    key_data = key
                    break

            if not key_data:
                raise ValueError(f"No matching key found for kid: {kid}")

            jwk = PyJWK.from_dict(key_data)
            public_key = jwk.key

            claims = pyjwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                options={"verify_exp": True}
            )
            return claims
        except pyjwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except pyjwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {e}")
