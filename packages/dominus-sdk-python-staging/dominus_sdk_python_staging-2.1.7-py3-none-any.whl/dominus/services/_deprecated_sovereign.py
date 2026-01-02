"""Sovereign Cloud service handler - Uses Bridge API"""
from ..helpers.core import execute_bridge_call, execute_with_retry, DominusResponse

# Bridge method map: command → (bridge_method, cacheable)
# All secrets/project operations go through the Bridge API at /newapi/bridge
# Auth operations (auth.self, auth.mint, auth.jwks) are handled separately via /newapi/auth
BRIDGE_METHODS = {
    # Secrets (via Bridge API)
    "secrets.get": ("secrets.get", True),
    "secrets.upsert": ("secrets.upsert", False),
}

# Legacy routes for non-bridge endpoints
LEGACY_ROUTES = {
    # Health (public, no auth needed)
    "sovereign.health.ping": ("GET", "/health", False, False),
    "sovereign.health.ready": ("GET", "/health/ready", False, False),

    # Project info - TODO: migrate to Bridge API
    "project.info": ("POST", "/api/project/info", True, True),
}


async def handle(command: str, token: str, sovereign_url: str, **kwargs) -> DominusResponse:
    """
    Handle Sovereign Cloud command.

    Uses Bridge API for secrets operations (JWT authenticated).
    Uses Crossover API for cross-project operations (JWT authenticated, admin scope).
    Falls back to legacy routes for health checks and project info.

    Args:
        command: Command name (e.g., "secrets.get", "crossover.secrets.get")
        token: PSK auth token (DOMINUS_TOKEN, used to get JWT)
        sovereign_url: Sovereign base URL
        **kwargs: Command parameters

    Returns:
        Response dict

    Raises:
        ValueError: If command is unknown or missing required parameters
        RuntimeError: If auth token is missing
    """
    # Check for crossover prefix
    if command.startswith("crossover."):
        # Extract method name (remove "crossover." prefix)
        method = command[10:]  # len("crossover.") = 10
        
        # Validate required parameters
        if "project_slug" not in kwargs:
            raise ValueError("crossover commands require 'project_slug' parameter")
        if "environment" not in kwargs:
            raise ValueError("crossover commands require 'environment' parameter")
        
        # Check if method is in BRIDGE_METHODS
        if method not in BRIDGE_METHODS:
            raise ValueError(f"Unknown crossover method: {method}. Available: {list(BRIDGE_METHODS.keys())}")
        
        bridge_method, cacheable = BRIDGE_METHODS[method]
        return await execute_bridge_call(
            method=bridge_method,
            base_url=sovereign_url,
            token=token,
            params=kwargs,
            cacheable=cacheable,
            endpoint="/newapi/crossover"
        )
    
    # Check Bridge API methods (own-project operations)
    if command in BRIDGE_METHODS:
        bridge_method, cacheable = BRIDGE_METHODS[command]
        return await execute_bridge_call(
            method=bridge_method,
            base_url=sovereign_url,
            token=token,
            params=kwargs,
            cacheable=cacheable
        )

    # Fall back to legacy routes
    if command in LEGACY_ROUTES:
        route_info = LEGACY_ROUTES[command]
        return await execute_with_retry(route_info, sovereign_url, token, kwargs)

    # Unknown command
    all_commands = list(BRIDGE_METHODS.keys()) + list(LEGACY_ROUTES.keys())
    crossover_commands = [f"crossover.{cmd}" for cmd in BRIDGE_METHODS.keys()]
    all_commands.extend(crossover_commands)
    raise ValueError(
        f"Unknown command: {command}. "
        f"Available: {all_commands}"
    )
