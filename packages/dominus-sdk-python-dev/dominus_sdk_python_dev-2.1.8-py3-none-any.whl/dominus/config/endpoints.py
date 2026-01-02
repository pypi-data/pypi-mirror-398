"""
Dominus Orchestrator Endpoints

Single backend URL for all services. The SDK now targets dominus-orchestrator
which consolidates all service functionality.

Usage:
    from dominus.config.endpoints import BASE_URL
"""

# Dominus Orchestrator Production URL
BASE_URL = "https://dominus-orchestrator-production-775398158805.us-east4.run.app"

# Legacy aliases (all point to orchestrator now) - DEPRECATED
SOVEREIGN_URL = BASE_URL
ARCHITECT_URL = BASE_URL
ORCHESTRATOR_URL = BASE_URL
WARDEN_URL = BASE_URL


def get_base_url() -> str:
    """Get the dominus-orchestrator base URL."""
    return BASE_URL


# DEPRECATED - use get_base_url()
def get_sovereign_url(environment: str = None) -> str:
    """Deprecated: Use get_base_url() instead."""
    return BASE_URL


def get_architect_url(environment: str = None) -> str:
    """Deprecated: Use get_base_url() instead."""
    return BASE_URL


def get_service_url(service: str, environment: str = None) -> str:
    """Deprecated: Use get_base_url() instead. All services are now consolidated."""
    return BASE_URL
