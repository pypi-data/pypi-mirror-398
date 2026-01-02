"""Architect Cloud service handler - Uses Bridge API and Crossover API"""
from ..helpers.core import execute_bridge_call, execute_command, DominusResponse, _ensure_valid_jwt, _b64_encode
import httpx

# Bridge method map: command → (bridge_method, cacheable)
# User-scoped operations go through Bridge API at /api/bridge
# These map to Architect's neon.* methods but with role-specific prefixes
# Note: Architect will extract project_id, branch_id, db_name from JWT claims
# The role parameter is derived from the command prefix (sql.app.* → role="app_user")
BRIDGE_METHODS = {
    # App user operations (app, config schemas in dominus DB)
    "sql.app.list_tables": ("neon.list_tables", True),
    "sql.app.query_table": ("neon.query_table_data", True),
    "sql.app.insert_row": ("neon.insert_row", False),
    "sql.app.update_rows": ("neon.update_rows", False),
    "sql.app.delete_rows": ("neon.delete_rows", False),
    "sql.app.list_columns": ("neon.list_columns", True),
    "sql.app.get_table_size": ("neon.get_table_size", True),

    # Secure user operations (secure, app schemas in dominus DB)
    "sql.secure.list_tables": ("neon.list_tables", True),
    "sql.secure.query_table": ("neon.query_table_data", True),
    "sql.secure.insert_row": ("neon.insert_row", False),
    "sql.secure.update_rows": ("neon.update_rows", False),
    "sql.secure.delete_rows": ("neon.delete_rows", False),  # Only app schema, not secure
    "sql.secure.list_columns": ("neon.list_columns", True),
    "sql.secure.get_table_size": ("neon.get_table_size", True),

    # Secure machine user operations (same as secure_user)
    "sql.secure_machine.list_tables": ("neon.list_tables", True),
    "sql.secure_machine.query_table": ("neon.query_table_data", True),
    "sql.secure_machine.insert_row": ("neon.insert_row", False),
    "sql.secure_machine.update_rows": ("neon.update_rows", False),
    "sql.secure_machine.delete_rows": ("neon.delete_rows", False),
    "sql.secure_machine.list_columns": ("neon.list_columns", True),
    "sql.secure_machine.get_table_size": ("neon.get_table_size", True),

    # Auth user operations (auth schema CRUD only in dominus DB)
    # All auth operations are NOT cached - admin UI needs fresh data
    # Scopes
    "auth.add_scope": ("auth.add_scope", False),
    "auth.delete_scope": ("auth.delete_scope", False),
    "auth.list_scopes": ("auth.list_scopes", False),
    "auth.get_scope": ("auth.get_scope", False),
    # Roles
    "auth.add_role": ("auth.add_role", False),
    "auth.delete_role": ("auth.delete_role", False),
    "auth.list_roles": ("auth.list_roles", False),
    "auth.get_role": ("auth.get_role", False),
    "auth.update_role_scopes": ("auth.update_role_scopes", False),
    # Users
    "auth.add_user": ("auth.add_user", False),
    "auth.delete_user": ("auth.delete_user", False),
    "auth.list_users": ("auth.list_users", False),
    "auth.get_user": ("auth.get_user", False),
    "auth.update_user_status": ("auth.update_user_status", False),
    "auth.update_user_role": ("auth.update_user_role", False),
    "auth.update_user": ("auth.update_user", False),
    "auth.update_user_password": ("auth.update_user_password", False),
    "auth.verify_user_password": ("auth.verify_user_password", False),
    # Clients (PSK)
    "auth.add_client": ("auth.add_client", False),
    "auth.delete_client": ("auth.delete_client", False),
    "auth.list_clients": ("auth.list_clients", False),
    "auth.get_client": ("auth.get_client", False),
    "auth.regenerate_client_psk": ("auth.regenerate_client_psk", False),
    "auth.verify_client_psk": ("auth.verify_client_psk", False),
    # Refresh tokens
    "auth.add_refresh_token": ("auth.add_refresh_token", False),
    "auth.delete_refresh_token": ("auth.delete_refresh_token", False),
    "auth.list_refresh_tokens": ("auth.list_refresh_tokens", False),
    # Frontend template methods
    "auth.check_page_access": ("auth.check_page_access", False),
    "auth.get_scope_navigation": ("auth.get_scope_navigation", False),
    "auth.get_user_navigation_scopes": ("auth.get_user_navigation_scopes", False),
    "auth.get_user_preferences": ("auth.get_user_preferences", False),
    "auth.set_user_preference": ("auth.set_user_preference", False),
    # Pages (auth.pages table - requires auth schema access)
    "auth.list_pages": ("auth.list_pages", False),
    "auth.get_page": ("auth.get_page", False),
    "auth.add_page": ("auth.add_page", False),
    "auth.update_page": ("auth.update_page", False),
    "auth.delete_page": ("auth.delete_page", False),
    "auth.get_page_scopes": ("auth.get_page_scopes", False),
    "auth.set_page_scopes": ("auth.set_page_scopes", False),
    # Navigation items (auth.nav_items table)
    "auth.list_nav_items": ("auth.list_nav_items", False),
    "auth.get_nav_item": ("auth.get_nav_item", False),
    "auth.add_nav_item": ("auth.add_nav_item", False),
    "auth.update_nav_item": ("auth.update_nav_item", False),
    "auth.delete_nav_item": ("auth.delete_nav_item", False),
    # Tenants (auth.tenants table)
    "auth.list_tenants": ("auth.list_tenants", False),
    "auth.get_tenant": ("auth.get_tenant", False),
    "auth.add_tenant": ("auth.add_tenant", False),
    "auth.update_tenant": ("auth.update_tenant", False),
    "auth.delete_tenant": ("auth.delete_tenant", False),
    "auth.get_tenant_users": ("auth.get_tenant_users", False),
    # Tenant categories (auth.tenant_categories table)
    "auth.list_tenant_categories": ("auth.list_tenant_categories", False),
    "auth.get_tenant_category": ("auth.get_tenant_category", False),
    "auth.add_tenant_category": ("auth.add_tenant_category", False),
    "auth.update_tenant_category": ("auth.update_tenant_category", False),
    "auth.delete_tenant_category": ("auth.delete_tenant_category", False),
    "auth.get_category_tenants": ("auth.get_category_tenants", False),
    # User junction tables (user_roles, user_scopes, user_tenants)
    "auth.get_user_roles": ("auth.get_user_roles", False),
    "auth.set_user_roles": ("auth.set_user_roles", False),
    "auth.get_user_scopes": ("auth.get_user_scopes", False),
    "auth.set_user_scopes": ("auth.set_user_scopes", False),
    "auth.get_user_tenants": ("auth.get_user_tenants", False),
    "auth.set_user_tenants": ("auth.set_user_tenants", False),
    # Role junction tables (role_scopes, role_tenants, role_categories)
    "auth.get_role_scopes": ("auth.get_role_scopes", False),
    "auth.set_role_tenants": ("auth.set_role_tenants", False),
    "auth.get_role_tenants": ("auth.get_role_tenants", False),
    "auth.set_role_categories": ("auth.set_role_categories", False),
    "auth.get_role_categories": ("auth.get_role_categories", False),

    # Schema user operations (DDL on app/secure, CRUD on meta in dominus DB)
    # App schema DDL
    "schema.add_table": ("schema.add_table", False),
    "schema.delete_table": ("schema.delete_table", False),
    "schema.list_tables": ("schema.list_tables", True),
    "schema.list_columns": ("schema.list_columns", True),
    "schema.add_column": ("schema.add_column", False),
    "schema.delete_column": ("schema.delete_column", False),
    # Secure schema DDL
    "schema.secure_add_table": ("schema.secure_add_table", False),
    "schema.secure_delete_table": ("schema.secure_delete_table", False),
    "schema.secure_list_tables": ("schema.secure_list_tables", True),
    "schema.secure_list_columns": ("schema.secure_list_columns", True),
    "schema.secure_add_column": ("schema.secure_add_column", False),
    "schema.secure_delete_column": ("schema.secure_delete_column", False),
}

# Crossover methods (admin-scoped, require admin JWT)
# Note: provision_complete removed from SDK - use Architect crossover API directly
CROSSOVER_METHODS = {
    # Placeholder for future admin-only methods
    # "sql.some_admin_op": ("admin.some_op", False),
}


async def _execute_bridge_with_sov_jwt(
    method: str,
    architect_url: str,
    sovereign_url: str,
    token: str,
    params: dict,
    cacheable: bool = False,
    endpoint: str = "/api/bridge",
) -> DominusResponse:
    """
    Bridge call that always mints the JWT from Sovereign but targets Architect.
    Avoids passing sovereign_url into execute_bridge_call for compatibility with older SDK installs.
    """
    # Mint JWT from Sovereign
    jwt = await _ensure_valid_jwt(token, sovereign_url)

    # Cache key (simple) if needed
    cache_key = None
    if cacheable and params:
        cache_key = f"bridge:{method}:{str(sorted(params.items()))}"
        from ..helpers.cache import dominus_cache
        cached = dominus_cache.get(cache_key)
        if cached:
            return cached

    # Prepare request
    headers = {
        "Authorization": f"Bearer {jwt}",
        "Content-Type": "text/plain",
    }
    body_b64 = _b64_encode({"method": method, "params": params})

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{architect_url}{endpoint}", content=body_b64, headers=headers)
        resp.raise_for_status()
        from ..helpers.core import _b64_decode
        result = _b64_decode(resp.text)

    if not result.get("success"):
        error_msg = result.get("error", "Unknown bridge error")
        raise RuntimeError(error_msg)

    data = result.get("data", {})
    if cache_key:
        dominus_cache.set(cache_key, data, ttl=300)
    return data


async def handle(command: str, token: str, architect_url: str, sovereign_url: str, **kwargs) -> DominusResponse:
    """
    Handle Architect Cloud command.
    
    Special case: sql.open.get_dsn - fetches DSN from Sovereign (not Architect endpoint)
    Crossover: crossover.sql.* - admin functions via /api/crossover
    Bridge: sql.* - user-scoped functions via /api/bridge
    
    Args:
        command: Command name (e.g., "sql.app.list_tables", "crossover.sql.provision_complete")
        token: PSK auth token (DOMINUS_TOKEN, used to get JWT)
        architect_url: Architect base URL
        sovereign_url: Sovereign base URL (for sql.open.get_dsn)
        **kwargs: Command parameters
        
    Returns:
        Response dict
        
    Raises:
        ValueError: If command is unknown or missing required parameters
        RuntimeError: If auth token is missing
    """
    # Special case: sql.open.get_dsn - get full DSN from Architect Bridge API
    if command == "sql.open.get_dsn":
        # Route through Architect Bridge API which constructs full DSN from Infisical
        # Architect uses provisioning token to access Infisical secrets for the user's project
        return await execute_bridge_call(
            method="sql.open.get_dsn",
            base_url=architect_url,
            token=token,
            params={},  # project_slug and environment extracted from JWT by bridge route
            cacheable=True,
            endpoint="/api/bridge",
            sovereign_url=sovereign_url,
        )
    
    # Check for crossover prefix (admin functions)
    # Note: Most admin operations (like provisioning) should go directly to Architect
    # This section is reserved for future admin methods that make sense in the SDK
    if command.startswith("crossover.sql."):
        # Extract method name (remove "crossover.sql." prefix)
        method = command[14:]  # len("crossover.sql.") = 14

        # Check if method is in CROSSOVER_METHODS
        if method not in CROSSOVER_METHODS:
            raise ValueError(
                f"Unknown crossover.sql method: {method}. "
                "Note: provision_complete has been removed from SDK. "
                "Use Architect's /api/crossover endpoint directly for provisioning."
            )

        bridge_method, cacheable = CROSSOVER_METHODS[method]
        return await execute_bridge_call(
            method=bridge_method,
            base_url=architect_url,
            token=token,
            params=kwargs,
            cacheable=cacheable,
            endpoint="/api/crossover",
            sovereign_url=sovereign_url,
        )
    
    # Check Bridge API methods (user-scoped operations)
    if command in BRIDGE_METHODS:
        bridge_method, cacheable = BRIDGE_METHODS[command]

        if command.startswith("auth."):
            # Auth routes already use auth_user role internally; don't add DB params that NeonService methods don't accept.
            # Filter out None values to avoid passing unnecessary null params that may cause issues on Architect Cloud
            params_with_context = {k: v for k, v in kwargs.items() if v is not None}
        else:
            # Determine role from command prefix
            # sql.app.* → role="app_user"
            # sql.secure.* → role="secure_user"
            # sql.secure_machine.* → role="secure_machine_user"
            # schema.* → role="schema_user"
            parts = command.split(".")

            if command.startswith("sql."):
                role_prefix = parts[1]  # sql.app.list_tables -> "app"
            elif command.startswith("schema."):
                role_prefix = "schema"
            else:
                role_prefix = "app"

            role_mapping = {
                "app": "app_user",
                "secure": "secure_user",
                "secure_machine": "secure_machine_user",
                "auth": "auth_user",
                "schema": "schema_user"
            }
            db_role = role_mapping.get(role_prefix, "app_user")

            # Determine default schema based on role
            schema_defaults = {
                "app": "app",
                "secure": "secure",
                "secure_machine": "secure",
                "auth": "auth",
                "schema": "app"  # Default to app schema for DDL, secure_ prefix overrides
            }
            default_schema = schema_defaults.get(role_prefix, "app")

            # Add role and default schema to params
            # Architect will extract project_id, branch_id, db_name from JWT
            params_with_context = {
                **kwargs,
                "role": db_role,
                "db_name": "dominus",  # All user-scoped operations use dominus DB
                "schema": kwargs.get("schema", default_schema)  # Allow override, but provide default
            }

        # Use a local helper to mint JWT from Sovereign and call Architect bridge without passing sovereign_url kwarg.
        return await _execute_bridge_with_sov_jwt(
            method=bridge_method,
            architect_url=architect_url,
            sovereign_url=sovereign_url,
            token=token,
            params=params_with_context,
            cacheable=cacheable,
        )
    
    # Unknown command
    all_commands = list(BRIDGE_METHODS.keys()) + ["sql.open.get_dsn"]
    crossover_commands = [f"crossover.sql.{cmd}" for cmd in CROSSOVER_METHODS.keys()]
    all_commands.extend(crossover_commands)
    raise ValueError(
        f"Unknown command: {command}. "
        f"Available: {all_commands}"
    )
