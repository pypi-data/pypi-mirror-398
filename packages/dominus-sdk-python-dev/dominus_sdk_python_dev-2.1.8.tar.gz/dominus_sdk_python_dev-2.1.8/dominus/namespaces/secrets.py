"""
Secrets Namespace - Warden secrets management.

Provides CRUD operations for secrets stored in the Warden service.
"""
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..start import Dominus


class SecretsNamespace:
    """
    Secrets management namespace.

    All secrets operations go through /api/warden/secrets endpoint.

    Usage:
        value = await dominus.secrets.get("API_KEY")
        await dominus.secrets.upsert("API_KEY", "secret_value")
        secrets = await dominus.secrets.list(prefix="DB_")
        await dominus.secrets.delete("OLD_KEY")
    """

    def __init__(self, client: "Dominus"):
        self._client = client

    async def get(self, key: str) -> Any:
        """
        Get a secret value.

        Args:
            key: Secret key name

        Returns:
            Secret value (usually string, but can be any JSON-serializable value)

        Raises:
            NotFoundError: If secret doesn't exist
        """
        result = await self._client._request(
            endpoint="/api/warden/secrets",
            body={"action": "get", "key": key}
        )
        # Response format: {"secret": {"key": "...", "value": "..."}}
        secret = result.get("secret", {})
        return secret.get("value")

    async def upsert(
        self,
        key: str,
        value: str,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create or update a secret.

        Tries update first, falls back to create if secret doesn't exist.

        Args:
            key: Secret key name
            value: Secret value
            comment: Optional comment/description

        Returns:
            Operation result with created/updated status
        """
        from ..errors import NotFoundError

        body = {"action": "update", "key": key, "value": value}
        if comment:
            body["comment"] = comment

        try:
            result = await self._client._request(
                endpoint="/api/warden/secrets",
                body=body
            )
            result["operation"] = "updated"
            return result
        except Exception as e:
            # If update fails (secret doesn't exist), try create
            if hasattr(e, 'status_code') and e.status_code == 500:
                body["action"] = "create"
                result = await self._client._request(
                    endpoint="/api/warden/secrets",
                    body=body
                )
                result["operation"] = "created"
                return result
            raise

    async def list(self, prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List secrets, optionally filtered by prefix.

        Args:
            prefix: Optional key prefix filter (e.g., "DB_" for all DB secrets)

        Returns:
            List of secret metadata (keys only, not values)
        """
        body = {"action": "list"}
        if prefix:
            body["prefix"] = prefix

        result = await self._client._request(
            endpoint="/api/warden/secrets",
            body=body
        )
        return result.get("secrets", [])

    async def delete(self, key: str) -> Dict[str, Any]:
        """
        Delete a secret.

        Args:
            key: Secret key to delete

        Returns:
            Operation result with deleted status
        """
        return await self._client._request(
            endpoint="/api/warden/secrets",
            body={"action": "delete", "key": key}
        )
