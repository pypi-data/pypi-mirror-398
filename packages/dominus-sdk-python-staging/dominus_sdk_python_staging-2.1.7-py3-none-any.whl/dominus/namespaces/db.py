"""
Database Namespace - Scribe data CRUD operations.

Provides data operations for all schemas with support for secure table access.
"""
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..start import Dominus


class DbNamespace:
    """
    Database CRUD namespace.

    All data operations go through /api/scribe/data/* endpoints.
    Secure tables (registered in auth.secure_tables) require a `reason` parameter.

    Usage:
        # List tables
        tables = await dominus.db.tables()
        tables = await dominus.db.tables(schema="tenant_acme")

        # Query with filters
        users = await dominus.db.query("users", filters={"status": "active"})

        # Query secure table (requires reason)
        patients = await dominus.db.query(
            "patients",
            schema="tenant_acme",
            reason="Reviewing chart for appointment #123",
            actor=current_user_id
        )

        # Insert data
        await dominus.db.insert("users", {"name": "John", "email": "john@example.com"})

        # Update rows
        await dominus.db.update("users", {"status": "inactive"}, filters={"id": user_id})

        # Delete rows
        await dominus.db.delete("users", filters={"id": user_id})
    """

    def __init__(self, client: "Dominus"):
        self._client = client

    async def tables(self, schema: str = "public") -> List[Dict[str, Any]]:
        """
        List tables in a schema.

        Args:
            schema: Schema name (default: "public")

        Returns:
            List of table metadata
        """
        result = await self._client._request(
            endpoint=f"/api/scribe/data/{schema}/tables",
            method="GET"
        )
        return result.get("tables", result) if isinstance(result, dict) else result

    async def columns(self, table: str, schema: str = "public") -> List[Dict[str, Any]]:
        """
        List columns in a table.

        Args:
            table: Table name
            schema: Schema name (default: "public")

        Returns:
            List of column metadata
        """
        result = await self._client._request(
            endpoint=f"/api/scribe/data/{schema}/{table}/columns",
            method="GET"
        )
        return result.get("columns", result) if isinstance(result, dict) else result

    async def query(
        self,
        table: str,
        schema: str = "public",
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "ASC",
        limit: int = 100,
        offset: int = 0,
        reason: Optional[str] = None,
        actor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query table data with filtering, sorting, and pagination.

        Args:
            table: Table name
            schema: Schema name (default: "public")
            filters: Column:value filter dictionary
            sort_by: Column to sort by
            sort_order: "ASC" or "DESC"
            limit: Maximum rows to return (default: 100)
            offset: Rows to skip (default: 0)
            reason: Access justification (required for secure tables)
            actor: User ID or "machine" for audit trail

        Returns:
            Dict with "rows" and "total" keys

        Raises:
            SecureTableError: If accessing secure table without reason
        """
        body = {
            "filters": filters,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "limit": limit,
            "offset": offset
        }

        if reason:
            body["reason"] = reason
        if actor:
            body["actor"] = actor

        return await self._client._request(
            endpoint=f"/api/scribe/data/{schema}/{table}/query",
            body=body
        )

    async def insert(
        self,
        table: str,
        data: Dict[str, Any],
        schema: str = "public",
        reason: Optional[str] = None,
        actor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Insert a row into a table.

        Args:
            table: Table name
            data: Column:value dictionary
            schema: Schema name (default: "public")
            reason: Access justification (required for secure tables)
            actor: User ID or "machine" for audit trail

        Returns:
            Inserted row data
        """
        body = {"data": data}

        if reason:
            body["reason"] = reason
        if actor:
            body["actor"] = actor

        return await self._client._request(
            endpoint=f"/api/scribe/data/{schema}/{table}/insert",
            body=body
        )

    async def update(
        self,
        table: str,
        data: Dict[str, Any],
        filters: Dict[str, Any],
        schema: str = "public",
        reason: Optional[str] = None,
        actor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update rows matching filters.

        Args:
            table: Table name
            data: Column:value dictionary of updates
            filters: Column:value dictionary for WHERE clause
            schema: Schema name (default: "public")
            reason: Access justification (required for secure tables)
            actor: User ID or "machine" for audit trail

        Returns:
            Dict with "affected_rows" count
        """
        body = {
            "data": data,
            "filters": filters
        }

        if reason:
            body["reason"] = reason
        if actor:
            body["actor"] = actor

        return await self._client._request(
            endpoint=f"/api/scribe/data/{schema}/{table}/update",
            body=body
        )

    async def delete(
        self,
        table: str,
        filters: Dict[str, Any],
        schema: str = "public",
        reason: Optional[str] = None,
        actor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete rows matching filters.

        Args:
            table: Table name
            filters: Column:value dictionary for WHERE clause
            schema: Schema name (default: "public")
            reason: Access justification (required for secure tables)
            actor: User ID or "machine" for audit trail

        Returns:
            Dict with "affected_rows" count
        """
        body = {"filters": filters}

        if reason:
            body["reason"] = reason
        if actor:
            body["actor"] = actor

        return await self._client._request(
            endpoint=f"/api/scribe/data/{schema}/{table}/delete",
            body=body
        )

    async def bulk_insert(
        self,
        table: str,
        rows: List[Dict[str, Any]],
        schema: str = "public",
        reason: Optional[str] = None,
        actor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Insert multiple rows at once.

        Args:
            table: Table name
            rows: List of column:value dictionaries
            schema: Schema name (default: "public")
            reason: Access justification (required for secure tables)
            actor: User ID or "machine" for audit trail

        Returns:
            Dict with "inserted_count" and optionally "rows"
        """
        body = {"rows": rows}

        if reason:
            body["reason"] = reason
        if actor:
            body["actor"] = actor

        return await self._client._request(
            endpoint=f"/api/scribe/data/{schema}/{table}/bulk-insert",
            body=body
        )

