"""
Token resolution helper.

Handles resolution of authentication token from environment variables.
No hardcoded tokens supported - environment variable only.
"""
import os
from typing import Optional


def _resolve_token() -> Optional[str]:
    """
    Resolve auth token from environment variable.

    Note: When fetching from Infisical via Sovereign, the secret is stored as
    PROVISION_DOMINUS_TOKEN but should be set as DOMINUS_TOKEN in environment.
    The PROVISION_ prefix is dropped when setting environment variables.

    Returns:
        Token string or None if not set
    """
    return os.getenv("DOMINUS_TOKEN")

