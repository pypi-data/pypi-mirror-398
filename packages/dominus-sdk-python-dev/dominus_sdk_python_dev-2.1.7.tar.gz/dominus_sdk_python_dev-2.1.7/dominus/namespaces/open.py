"""
Open Namespace - Direct database access operations.

Provides DSN retrieval and raw SQL execution for advanced use cases.
"""
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..start import Dominus


class OpenNamespace:
    """
    Open database access namespace.

    Provides direct database connection info and raw SQL execution.
    Use with caution - bypasses most safety checks.

    Usage:
        # Get connection DSN
        dsn = await dominus.open.dsn()

        # Execute raw SQL
        result = await dominus.open.execute("SELECT * FROM public.users WHERE id = $1", {"1": user_id})
    """

    def __init__(self, client: "Dominus"):
        self._client = client

    async def dsn(self) -> str:
        """
        Get the PostgreSQL connection DSN.

        Returns the complete PostgreSQL connection URI that can be
        used directly by clients to connect to the database.

        Returns:
            PostgreSQL connection URI string
        """
        result = await self._client._request(
            endpoint="/api/scribe/open/dsn",
            method="GET"
        )
        if isinstance(result, dict):
            return result.get("dsn", result.get("connection_string", ""))
        return result

    async def execute(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute raw SQL query.

        Use with caution - this bypasses most safety checks.

        Args:
            sql: SQL query string
            params: Optional parameter dictionary

        Returns:
            Query result
        """
        body = {"sql": sql}
        if params:
            body["params"] = params

        return await self._client._request(
            endpoint="/api/scribe/open/execute",
            body=body
        )
