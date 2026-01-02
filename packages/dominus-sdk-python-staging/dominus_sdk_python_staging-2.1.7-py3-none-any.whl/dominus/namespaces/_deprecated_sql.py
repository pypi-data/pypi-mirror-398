"""SQL operations namespace - Role-based database operations"""
from typing import Dict, Any, List, Optional

from ..helpers.crypto import hash_password, hash_psk, hash_token, generate_token


class SQLNamespace:
    """SQL operations namespace"""

    def __init__(self, _execute_command, _execute_sovereign_command=None):
        """
        Initialize SQL namespace.

        Args:
            _execute_command: Internal function to execute commands (routes to Architect)
            _execute_sovereign_command: Internal function for Sovereign commands (optional)
        """
        self._execute = _execute_command
        self._execute_sovereign = _execute_sovereign_command
        self.app = SQLRoleNamespace("app", _execute_command)
        self.secure = SQLRoleNamespace("secure", _execute_command)
        self.secure_machine = SQLRoleNamespace("secure_machine", _execute_command)
        self.auth = SQLAuthNamespace(_execute_command, _execute_sovereign_command)
        self.schema = SQLSchemaNamespace(_execute_command)
        self.open = SQLOpenNamespace(_execute_command)


class SQLRoleNamespace:
    """Role-specific SQL operations (app_user, secure_user, secure_machine_user)"""
    
    def __init__(self, role: str, _execute_command):
        """
        Initialize role namespace.
        
        Args:
            role: Role name ("app", "secure", "secure_machine")
            _execute_command: Internal function to execute commands
        """
        self._role = role
        self._command_prefix = f"sql.{role}"
        self._execute = _execute_command
        self._default_schema = "app" if role == "app" else "secure"
    
    async def list_tables(self, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List tables in a schema.
        
        Args:
            schema: Schema name (default: "app" for app_user, "secure" for secure_user)
        
        Returns:
            List of table information dictionaries
        """
        if schema is None:
            schema = self._default_schema
        command = f"{self._command_prefix}.list_tables"
        return await self._execute(command, schema=schema)
    
    async def query_table(
        self,
        table_name: str,
        schema: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "ASC",
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Query table data with pagination and filters.
        
        Args:
            table_name: Table name
            schema: Schema name (default: "app" for app_user, "secure" for secure_user)
            filters: Optional dictionary of column:value filters
            sort_by: Optional column name to sort by
            sort_order: Sort order (ASC or DESC, default: ASC)
            limit: Maximum number of rows to return (default: 100)
            offset: Number of rows to skip (default: 0)
        
        Returns:
            Dictionary with 'rows' and 'total' keys
        """
        if schema is None:
            schema = self._default_schema
        command = f"{self._command_prefix}.query_table"
        return await self._execute(
            command,
            table_name=table_name,
            schema=schema,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
    
    async def insert_row(
        self,
        table_name: str,
        data: Dict[str, Any],
        schema: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Insert a single row into a table.
        
        Args:
            table_name: Table name
            data: Dictionary of column:value pairs
            schema: Schema name (default: "app" for app_user, "secure" for secure_user)
        
        Returns:
            Dictionary with inserted row data
        """
        if schema is None:
            schema = self._default_schema
        command = f"{self._command_prefix}.insert_row"
        return await self._execute(
            command,
            table_name=table_name,
            data=data,
            schema=schema
        )
    
    async def update_rows(
        self,
        table_name: str,
        data: Dict[str, Any],
        filters: Dict[str, Any],
        schema: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update rows matching filters.
        
        Args:
            table_name: Table name
            data: Dictionary of column:value pairs to update
            filters: Dictionary of column:value pairs for WHERE clause
            schema: Schema name (default: "app" for app_user, "secure" for secure_user)
        
        Returns:
            Dictionary with 'affected_rows' key
        """
        if schema is None:
            schema = self._default_schema
        command = f"{self._command_prefix}.update_rows"
        return await self._execute(
            command,
            table_name=table_name,
            data=data,
            filters=filters,
            schema=schema
        )
    
    async def delete_rows(
        self,
        table_name: str,
        filters: Dict[str, Any],
        schema: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete rows matching filters.
        
        Note: For secure_user and secure_machine_user, DELETE only works on app schema,
        not on secure schema (PHI data uses soft deletes only).
        
        Args:
            table_name: Table name
            filters: Dictionary of column:value pairs for WHERE clause
            schema: Schema name (default: "app" - secure roles can only delete from app schema)
        
        Returns:
            Dictionary with 'affected_rows' key
        """
        if schema is None:
            schema = "app"  # Always app for delete operations (secure schema doesn't allow DELETE)
        command = f"{self._command_prefix}.delete_rows"
        return await self._execute(
            command,
            table_name=table_name,
            filters=filters,
            schema=schema
        )
    
    async def list_columns(
        self,
        table_name: str,
        schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List columns in a table.
        
        Args:
            table_name: Table name
            schema: Schema name (default: "app" for app_user, "secure" for secure_user)
        
        Returns:
            List of column information dictionaries
        """
        if schema is None:
            schema = self._default_schema
        command = f"{self._command_prefix}.list_columns"
        return await self._execute(
            command,
            table_name=table_name,
            schema=schema
        )
    
    async def get_table_size(
        self,
        table_name: str,
        schema: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get table size information.
        
        Args:
            table_name: Table name
            schema: Schema name (default: "app" for app_user, "secure" for secure_user)
        
        Returns:
            Dictionary with table size information
        """
        if schema is None:
            schema = self._default_schema
        command = f"{self._command_prefix}.get_table_size"
        return await self._execute(
            command,
            table_name=table_name,
            schema=schema
        )


class SQLOpenNamespace:
    """Open user namespace - Returns DSN string for dominus_open database"""

    def __init__(self, _execute_command):
        """
        Initialize open namespace.

        Args:
            _execute_command: Internal function to execute commands
        """
        self._execute = _execute_command

    async def dsn(self) -> str:
        """
        Get the full DSN connection string for open_user role.

        This returns the complete PostgreSQL connection URI for the dominus_open
        database that can be used directly by clients to connect.

        Returns:
            PostgreSQL connection URI string in format:
            postgresql://{userpwcombo}@{branchtargetstring}/dominus_open?sslmode=require&channel_binding=require

        Note:
            This is the only role that exposes the DSN string directly.
            All other roles use the DSN internally for operations.
        """
        return await self._execute("sql.open.get_dsn")


class SQLAuthNamespace:
    """
    Authentication operations namespace.

    Provides scoped functions for managing auth schema tables:
    - scopes: Permission definitions
    - roles: Role definitions with assigned scopes
    - users: User accounts with assigned roles
    - clients: Service account PSKs with assigned roles
    - refresh_tokens: Token management
    - JWT operations: Minting and validation

    DB User: auth_user (CRUD on auth schema only)
    """

    def __init__(self, _execute_command, _execute_sovereign_command=None):
        """
        Initialize auth namespace.

        Args:
            _execute_command: Internal function to execute commands (Architect)
            _execute_sovereign_command: Internal function for Sovereign commands
        """
        self._execute = _execute_command
        self._execute_sovereign = _execute_sovereign_command
        self._public_key_cache = None

    # ========================================
    # SCOPES (auth.scopes table)
    # ========================================

    async def add_scope(
        self,
        slug: str,
        display_name: str,
        category_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a new scope.

        Args:
            slug: Unique scope identifier (e.g., "read", "write", "admin")
            display_name: Human-readable name
            category_id: Optional tenant category UUID to link via scope_categories
            description: Optional description

        Returns:
            Created scope record
        """
        return await self._execute(
            "auth.add_scope",
            slug=slug,
            display_name=display_name,
            category_id=category_id,
            description=description
        )

    async def delete_scope(self, scope_id: str) -> Dict[str, Any]:
        """
        Delete a scope by ID.

        Args:
            scope_id: UUID of scope to delete

        Returns:
            Deletion confirmation
        """
        return await self._execute("auth.delete_scope", scope_id=scope_id)

    async def list_scopes(
        self,
        category_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all scopes, optionally filtered by category.

        Args:
            category_id: Optional tenant category UUID filter

        Returns:
            List of scope records
        """
        return await self._execute(
            "auth.list_scopes",
            category_id=category_id
        )

    async def get_scope(
        self,
        scope_id: Optional[str] = None,
        slug: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a scope by ID or slug.

        Args:
            scope_id: UUID of scope (preferred)
            slug: Scope slug (alternative lookup)

        Returns:
            Scope record
        """
        return await self._execute(
            "auth.get_scope",
            scope_id=scope_id,
            slug=slug
        )

    # ========================================
    # ROLES (auth.roles table)
    # ========================================

    async def add_role(
        self,
        name: str,
        scope_slugs: Optional[List[str]] = None,
        description: Optional[str] = None,
        tenant_id: Optional[str] = None,
        category_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a new role.

        Args:
            name: Role name (unique per tenant)
            scope_slugs: List of scope slugs to assign
            description: Optional description
            tenant_id: Optional tenant UUID to link via role_tenants
            category_id: Optional category UUID to link via role_categories

        Returns:
            Created role record
        """
        return await self._execute(
            "auth.add_role",
            name=name,
            scope_slugs=scope_slugs or [],
            description=description,
            tenant_id=tenant_id,
            category_id=category_id
        )

    async def delete_role(self, role_id: str) -> Dict[str, Any]:
        """
        Delete a role by ID.

        Args:
            role_id: UUID of role to delete

        Returns:
            Deletion confirmation
        """
        return await self._execute("auth.delete_role", role_id=role_id)

    async def list_roles(self) -> List[Dict[str, Any]]:
        """
        List all roles for the tenant.

        Returns:
            List of role records
        """
        return await self._execute("auth.list_roles")

    async def get_role(
        self,
        role_id: Optional[str] = None,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a role by ID or name.

        Args:
            role_id: UUID of role (preferred)
            name: Role name (alternative lookup)

        Returns:
            Role record
        """
        return await self._execute(
            "auth.get_role",
            role_id=role_id,
            name=name
        )

    async def update_role_scopes(
        self,
        role_id: str,
        scope_slugs: List[str]
    ) -> Dict[str, Any]:
        """
        Update the scopes assigned to a role.

        Args:
            role_id: UUID of role to update
            scope_slugs: New list of scope slugs

        Returns:
            Updated role record
        """
        return await self._execute(
            "auth.update_role_scopes",
            role_id=role_id,
            scope_slugs=scope_slugs
        )

    # ========================================
    # USERS (auth.users table)
    # ========================================

    async def add_user(
        self,
        username: str,
        password: str,
        role_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a new user.

        Password is hashed client-side before sending to Architect.

        Args:
            username: Unique username
            password: Raw password (will be hashed)
            role_id: Optional UUID of role to assign
            tenant_id: Optional UUID of tenant to link (defaults from role if provided)
            email: Optional email address

        Returns:
            Created user record (without password_hash)
        """
        password_hash = hash_password(password)
        return await self._execute(
            "auth.add_user",
            username=username,
            password_hash=password_hash,
            role_id=role_id,
            tenant_id=tenant_id,
            email=email
        )

    async def delete_user(self, user_id: str) -> Dict[str, Any]:
        """
        Delete a user by ID.

        Args:
            user_id: UUID of user to delete

        Returns:
            Deletion confirmation
        """
        return await self._execute("auth.delete_user", user_id=user_id)

    async def list_users(self) -> List[Dict[str, Any]]:
        """
        List all users for the tenant.

        Returns:
            List of user records (without password_hash)
        """
        return await self._execute("auth.list_users")

    async def get_user(
        self,
        user_id: Optional[str] = None,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a user by ID or username.

        Args:
            user_id: UUID of user (preferred)
            username: Username (alternative lookup)

        Returns:
            User record (without password_hash)
        """
        return await self._execute(
            "auth.get_user",
            user_id=user_id,
            username=username
        )

    async def update_user_status(
        self,
        user_id: str,
        status: str
    ) -> Dict[str, Any]:
        """
        Update a user's status.

        Args:
            user_id: UUID of user to update
            status: New status (e.g., "active", "inactive", "suspended")

        Returns:
            Updated user record
        """
        return await self._execute(
            "auth.update_user_status",
            user_id=user_id,
            status=status
        )

    async def update_user_role(
        self,
        user_id: str,
        role_id: str
    ) -> Dict[str, Any]:
        """
        Update a user's assigned role.

        Args:
            user_id: UUID of user to update
            role_id: UUID of new role

        Returns:
            Updated user record
        """
        return await self._execute(
            "auth.update_user_role",
            user_id=user_id,
            role_id=role_id
        )

    async def update_user(
        self,
        user_id: str,
        username: str = None,
        email: str = None
    ) -> Dict[str, Any]:
        """
        Update a user's profile fields (username, email).

        Args:
            user_id: UUID of user to update
            username: New username (optional)
            email: New email (optional, can be None to clear)

        Returns:
            Updated user record
        """
        params = {"user_id": user_id}
        if username is not None:
            params["username"] = username
        if email is not None:
            params["email"] = email
        return await self._execute("auth.update_user", **params)

    async def update_user_password(
        self,
        user_id: str,
        password: str
    ) -> Dict[str, Any]:
        """
        Update a user's password.

        Args:
            user_id: UUID of user to update
            password: New raw password (will be hashed by Architect)

        Returns:
            Updated user record (without password_hash)
        """
        return await self._execute(
            "auth.update_user_password",
            user_id=user_id,
            password=password
        )

    async def verify_user_password(
        self,
        username: str,
        password: str
    ) -> Dict[str, Any]:
        """
        Verify a user's password.

        Raw password is sent to Architect which does bcrypt comparison.

        Args:
            username: Username to verify
            password: Raw password to check

        Returns:
            {"valid": True/False, "user": {...}} if valid
        """
        return await self._execute(
            "auth.verify_user_password",
            username=username,
            password=password
        )

    # ========================================
    # CLIENTS / PSK (auth.client_psk table)
    # ========================================

    async def add_client(
        self,
        label: str,
        role_id: str
    ) -> Dict[str, Any]:
        """
        Add a new service client with PSK.

        Generates a PSK, hashes it, stores the hash, and returns
        the raw PSK (one-time visible).

        Args:
            label: Human-readable label for the client
            role_id: UUID of role to assign

        Returns:
            {"client": {...}, "psk": "raw-psk-one-time-visible"}
        """
        from ..helpers.crypto import generate_psk_local
        # Generate PSK (prefer Sovereign route if available, fallback to local)
        if self._execute_sovereign:
            try:
                result = await self._execute_sovereign("auth.generate_psk")
                raw_psk = result.get("psk")
            except Exception:
                raw_psk = generate_psk_local()
        else:
            raw_psk = generate_psk_local()

        psk_hash = hash_psk(raw_psk)
        client_result = await self._execute(
            "auth.add_client",
            label=label,
            role_id=role_id,
            psk_hash=psk_hash
        )
        return {
            "client": client_result,
            "psk": raw_psk  # One-time visible
        }

    async def delete_client(self, client_id: str) -> Dict[str, Any]:
        """
        Delete a client by ID.

        Args:
            client_id: UUID of client to delete

        Returns:
            Deletion confirmation
        """
        return await self._execute("auth.delete_client", client_id=client_id)

    async def list_clients(self) -> List[Dict[str, Any]]:
        """
        List all clients for the tenant.

        Returns:
            List of client records (without psk_hash)
        """
        return await self._execute("auth.list_clients")

    async def get_client(self, client_id: str) -> Dict[str, Any]:
        """
        Get a client by ID.

        Args:
            client_id: UUID of client

        Returns:
            Client record (without psk_hash)
        """
        return await self._execute("auth.get_client", client_id=client_id)

    async def regenerate_client_psk(self, client_id: str) -> Dict[str, Any]:
        """
        Regenerate a client's PSK.

        Generates a new PSK, hashes it, updates the stored hash,
        and returns the new raw PSK (one-time visible).

        Args:
            client_id: UUID of client

        Returns:
            {"client": {...}, "psk": "new-raw-psk-one-time-visible"}
        """
        from ..helpers.crypto import generate_psk_local
        # Generate new PSK
        if self._execute_sovereign:
            try:
                result = await self._execute_sovereign("auth.generate_psk")
                raw_psk = result.get("psk")
            except Exception:
                raw_psk = generate_psk_local()
        else:
            raw_psk = generate_psk_local()

        psk_hash = hash_psk(raw_psk)
        client_result = await self._execute(
            "auth.regenerate_client_psk",
            client_id=client_id,
            psk_hash=psk_hash
        )
        return {
            "client": client_result,
            "psk": raw_psk  # One-time visible
        }

    async def verify_client_psk(
        self,
        client_id: str,
        psk: str
    ) -> Dict[str, Any]:
        """
        Verify a client's PSK.

        Raw PSK is sent to Architect which does bcrypt comparison.

        Args:
            client_id: UUID of client
            psk: Raw PSK to verify

        Returns:
            {"valid": True/False, "client": {...}} if valid
        """
        return await self._execute(
            "auth.verify_client_psk",
            client_id=client_id,
            psk=psk
        )

    # ========================================
    # REFRESH TOKENS (auth.refresh_tokens table)
    # ========================================

    async def add_refresh_token(
        self,
        user_id: Optional[str] = None,
        client_psk_id: Optional[str] = None,
        expires_in_seconds: int = 86400 * 30  # 30 days default
    ) -> Dict[str, Any]:
        """
        Create a new refresh token.

        Either user_id or client_psk_id must be provided.

        Args:
            user_id: UUID of user (for user tokens)
            client_psk_id: UUID of client (for service tokens)
            expires_in_seconds: Token lifetime (default: 30 days)

        Returns:
            {"token_id": "...", "token": "raw-token-one-time-visible"}
        """
        raw_token = generate_token()
        token_hash = hash_token(raw_token)

        result = await self._execute(
            "auth.add_refresh_token",
            user_id=user_id,
            client_psk_id=client_psk_id,
            token_hash=token_hash,
            expires_in_seconds=expires_in_seconds
        )
        return {
            "token_id": result.get("id"),
            "token": raw_token,  # One-time visible
            "expires_at": result.get("expires_at")
        }

    async def delete_refresh_token(self, token_id: str) -> Dict[str, Any]:
        """
        Delete/revoke a refresh token.

        Args:
            token_id: UUID of token to delete

        Returns:
            Deletion confirmation
        """
        return await self._execute(
            "auth.delete_refresh_token",
            token_id=token_id
        )

    async def list_refresh_tokens(
        self,
        user_id: Optional[str] = None,
        client_psk_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List refresh tokens, optionally filtered.

        Args:
            user_id: Filter by user
            client_psk_id: Filter by client

        Returns:
            List of token records (without token_hash)
        """
        return await self._execute(
            "auth.list_refresh_tokens",
            user_id=user_id,
            client_psk_id=client_psk_id
        )

    # ========================================
    # JWT OPERATIONS (via Sovereign)
    # ========================================

    async def mint_subsidiary_jwt(
        self,
        user_id: str,
        scope: Optional[List[str]] = None,
        expires_in: int = 900,
        system: str = "user"
    ) -> Dict[str, Any]:
        """
        Mint a JWT for a subsidiary user.

        Uses DOMINUS_TOKEN to authenticate with Sovereign, then
        requests a JWT with the specified subsidiary user_id.

        Args:
            user_id: Subsidiary user identifier to embed in JWT
            scope: List of scopes to include
            expires_in: Token lifetime in seconds (default: 15 min)
            system: System identifier (default: "user")

        Returns:
            {"access_token": "...", "token_type": "Bearer", "expires_in": ...}
        """
        if not self._execute_sovereign:
            raise RuntimeError("Sovereign command executor not available")

        return await self._execute_sovereign(
            "auth.mint_token",
            user_id=user_id,
            scope=scope,
            system=system
        )

    async def get_public_key(self) -> str:
        """
        Get Sovereign's public key for JWT validation.

        Caches the key after first fetch.

        Returns:
            PEM-encoded public key string
        """
        if self._public_key_cache:
            return self._public_key_cache

        if not self._execute_sovereign:
            raise RuntimeError("Sovereign command executor not available")

        result = await self._execute_sovereign("auth.get_public_key")
        self._public_key_cache = result.get("public_key")
        return self._public_key_cache

    async def validate_jwt(self, token: str) -> Dict[str, Any]:
        """
        Validate a JWT and return its claims.

        Fetches public key from Sovereign (cached) and validates locally.

        Args:
            token: JWT string to validate

        Returns:
            Decoded JWT claims if valid

        Raises:
            ValueError: If token is invalid or expired
        """
        import jwt as pyjwt

        public_key = await self.get_public_key()

        try:
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

    # ========================================
    # PAGE ACCESS CONTROL (auth.pages table)
    # ========================================

    async def check_page_access(
        self,
        page_path: str,
        user_jwt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if user has access to a specific page.

        Args:
            page_path: Page path (e.g., "/dashboard/admin")
            user_jwt: Optional user's JWT token (for extracting scopes)

        Returns:
            {
                "allowed": bool,
                "reason": str (optional, if not allowed)
            }

        Logic (handled by Architect backend):
        1. Query auth.pages for page_id
        2. If page not found, return allowed=True (unregistered pages are open)
        3. Extract scopes from user JWT
        4. Compare JWT scopes with page's required_scopes
        5. Return access decision
        """
        return await self._execute(
            "auth.check_page_access",
            page_path=page_path,
            user_jwt=user_jwt
        )

    # ========================================
    # SCOPE NAVIGATION (auth.scope_navigation table)
    # ========================================

    async def get_scope_navigation(
        self,
        scope_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get navigation items for a specific scope.

        Args:
            scope_id: UUID of the scope

        Returns:
            List of navigation items (from auth.scope_navigation table)
            Sorted by order field
        """
        return await self._execute(
            "auth.get_scope_navigation",
            scope_id=scope_id
        )

    async def get_user_navigation_scopes(
        self,
        user_id: str,
        jwt_scopes: List[str],
        tenant_category_name: str = 'admin'
    ) -> List[Dict[str, Any]]:
        """
        Get all navigation scopes available to a user.

        Args:
            user_id: User UUID
            jwt_scopes: List of scope slugs from user's JWT
            tenant_category_name: Name of tenant category to filter by (default: 'admin')

        Returns:
            List of Scope objects for navigation
            Filtered by:
            - tenant_category_id = category matching tenant_category_name
            - scope slug in jwt_scopes
        """
        return await self._execute(
            "auth.get_user_navigation_scopes",
            user_id=user_id,
            jwt_scopes=jwt_scopes,
            tenant_category_name=tenant_category_name
        )

    # ========================================
    # USER PREFERENCES (auth.user_preferences table)
    # ========================================

    async def get_user_preferences(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get user preferences from auth.user_preferences table.

        Args:
            user_id: User UUID

        Returns:
            Preferences JSONB object (defaults to empty dict if not found)
        """
        result = await self._execute(
            "auth.get_user_preferences",
            user_id=user_id
        )
        # Return empty dict if not found, otherwise return preferences
        return result.get("preferences", {}) if result else {}

    async def set_user_preference(
        self,
        user_id: str,
        key: str,
        value: Any
    ) -> Dict[str, Any]:
        """
        Set a user preference.

        Args:
            user_id: User UUID
            key: Preference key (e.g., "default_scope_id", "theme")
            value: Preference value

        Returns:
            Updated preferences object
        """
        return await self._execute(
            "auth.set_user_preference",
            user_id=user_id,
            key=key,
            value=value
        )


class SQLSchemaNamespace:
    """
    Schema DDL operations namespace.

    Provides functions for managing table structure in app and secure schemas:
    - Create/drop tables
    - Add/drop columns
    - List tables and columns

    DB User: schema_user (DDL on app/secure, CRUD on meta)
    """

    def __init__(self, _execute_command):
        """
        Initialize schema namespace.

        Args:
            _execute_command: Internal function to execute commands
        """
        self._execute = _execute_command

    # ========================================
    # APP SCHEMA (default)
    # ========================================

    async def add_table(
        self,
        table_name: str,
        columns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create a new table in the app schema.

        Args:
            table_name: Name of table to create
            columns: List of column definitions
                [{"name": "id", "type": "UUID", "constraints": ["PRIMARY KEY"]}]

        Returns:
            Creation confirmation
        """
        return await self._execute(
            "schema.add_table",
            table_name=table_name,
            columns=columns
        )

    async def delete_table(self, table_name: str) -> Dict[str, Any]:
        """
        Drop a table from the app schema.

        Args:
            table_name: Name of table to drop

        Returns:
            Deletion confirmation
        """
        return await self._execute(
            "schema.delete_table",
            table_name=table_name
        )

    async def list_tables(self) -> List[Dict[str, Any]]:
        """
        List all tables in the app schema.

        Returns:
            List of table information
        """
        return await self._execute("schema.list_tables")

    async def list_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """
        List columns in a table in the app schema.

        Args:
            table_name: Name of table

        Returns:
            List of column information
        """
        return await self._execute(
            "schema.list_columns",
            table_name=table_name
        )

    async def add_column(
        self,
        table_name: str,
        column_name: str,
        column_type: str,
        constraints: Optional[List[str]] = None,
        default: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a column to a table in the app schema.

        Args:
            table_name: Name of table
            column_name: Name of new column
            column_type: PostgreSQL type (e.g., "VARCHAR(100)", "INTEGER")
            constraints: Optional constraints (e.g., ["NOT NULL"])
            default: Optional default value

        Returns:
            Alteration confirmation
        """
        return await self._execute(
            "schema.add_column",
            table_name=table_name,
            column_name=column_name,
            column_type=column_type,
            constraints=constraints,
            default=default
        )

    async def delete_column(
        self,
        table_name: str,
        column_name: str
    ) -> Dict[str, Any]:
        """
        Drop a column from a table in the app schema.

        Args:
            table_name: Name of table
            column_name: Name of column to drop

        Returns:
            Alteration confirmation
        """
        return await self._execute(
            "schema.delete_column",
            table_name=table_name,
            column_name=column_name
        )

    # ========================================
    # SECURE SCHEMA (explicit prefix)
    # ========================================

    async def secure_add_table(
        self,
        table_name: str,
        columns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create a new table in the secure schema.

        Args:
            table_name: Name of table to create
            columns: List of column definitions

        Returns:
            Creation confirmation
        """
        return await self._execute(
            "schema.secure_add_table",
            table_name=table_name,
            columns=columns
        )

    async def secure_delete_table(self, table_name: str) -> Dict[str, Any]:
        """
        Drop a table from the secure schema.

        Args:
            table_name: Name of table to drop

        Returns:
            Deletion confirmation
        """
        return await self._execute(
            "schema.secure_delete_table",
            table_name=table_name
        )

    async def secure_list_tables(self) -> List[Dict[str, Any]]:
        """
        List all tables in the secure schema.

        Returns:
            List of table information
        """
        return await self._execute("schema.secure_list_tables")

    async def secure_list_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """
        List columns in a table in the secure schema.

        Args:
            table_name: Name of table

        Returns:
            List of column information
        """
        return await self._execute(
            "schema.secure_list_columns",
            table_name=table_name
        )

    async def secure_add_column(
        self,
        table_name: str,
        column_name: str,
        column_type: str,
        constraints: Optional[List[str]] = None,
        default: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a column to a table in the secure schema.

        Args:
            table_name: Name of table
            column_name: Name of new column
            column_type: PostgreSQL type
            constraints: Optional constraints
            default: Optional default value

        Returns:
            Alteration confirmation
        """
        return await self._execute(
            "schema.secure_add_column",
            table_name=table_name,
            column_name=column_name,
            column_type=column_type,
            constraints=constraints,
            default=default
        )

    async def secure_delete_column(
        self,
        table_name: str,
        column_name: str
    ) -> Dict[str, Any]:
        """
        Drop a column from a table in the secure schema.

        Args:
            table_name: Name of table
            column_name: Name of column to drop

        Returns:
            Alteration confirmation
        """
        return await self._execute(
            "schema.secure_delete_column",
            table_name=table_name,
            column_name=column_name
        )
