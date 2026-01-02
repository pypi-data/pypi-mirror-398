"""
Core HTTP client, routing, and retry logic.

Includes circuit breaker pattern to prevent runaway retries from exhausting
Cloud Run CPU quota during service outages or circular dependency issues.
"""
import asyncio
import httpx
import base64
import json
import time
from typing import Any, Optional

from .cache import dominus_cache, sovereign_circuit_breaker, exponential_backoff_with_jitter

# Max retries for HTTP requests (reduced from implicit to explicit)
MAX_RETRIES = 3

# Type alias
DominusResponse = dict[str, Any]

# Base64 helpers
# Encode: Convert dict to JSON, then to raw base64 string (matches middleware expectation)
_b64_encode = lambda d: base64.b64encode(json.dumps(d).encode()).decode()
# Decode: Decode raw base64 string to JSON, then parse (matches middleware response format)
_b64_decode = lambda s: json.loads(base64.b64decode(s.encode('utf-8')).decode('utf-8')) if isinstance(s, str) else s
_b64_token = lambda t: base64.b64encode(t.encode()).decode()

# Base64url helpers for JWT
def _b64url_decode(s: str) -> bytes:
    """Decode base64url string (JWT uses base64url, not base64)."""
    # Add padding if needed
    padding = 4 - len(s) % 4
    if padding != 4:
        s += '=' * padding
    # Replace URL-safe characters
    s = s.replace('-', '+').replace('_', '/')
    return base64.b64decode(s)


def _decode_jwt_payload(jwt: str) -> dict:
    """
    Decode JWT payload without verification (for exp checks only).
    
    Args:
        jwt: JWT token string
        
    Returns:
        Decoded payload dict
    """
    try:
        parts = jwt.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")
        payload_b64url = parts[1]
        payload_bytes = _b64url_decode(payload_b64url)
        return json.loads(payload_bytes.decode('utf-8'))
    except Exception as e:
        raise ValueError(f"Failed to decode JWT payload: {e}")


async def _get_service_jwt(psk_token: str, base_url: str) -> str:
    """
    Get service JWT by calling /api/warden/mint with PSK.

    Uses circuit breaker to prevent retry storms during service outages.
    Retries on 401/5xx with exponential backoff (orchestrator cold start handling).

    Args:
        psk_token: PSK token (DOMINUS_TOKEN)
        base_url: Orchestrator base URL

    Returns:
        JWT token string

    Raises:
        RuntimeError: If circuit is open or auth fails after retries
    """
    # Circuit breaker check
    if not sovereign_circuit_breaker.can_execute():
        raise RuntimeError(
            f"Circuit breaker OPEN for auth - "
            f"too many recent failures. Will retry after recovery timeout."
        )

    if sovereign_circuit_breaker.state == sovereign_circuit_breaker.HALF_OPEN:
        sovereign_circuit_breaker.record_half_open_call()

    headers = {
        "Authorization": f"Bearer {psk_token}",
        "Content-Type": "text/plain"
    }

    # Body format for warden/mint endpoint
    body_json = {"method": "auth.self", "params": {}}
    body_b64 = _b64_encode(body_json)

    # Retry loop for JWT minting (handles orchestrator cold start)
    JWT_MINT_RETRIES = 3
    last_error = None

    for attempt in range(JWT_MINT_RETRIES):
        try:
            async with httpx.AsyncClient(base_url=base_url, headers=headers, timeout=30.0) as client:
                response = await client.post("/api/warden/mint", content=body_b64)

                # Check for retryable status codes before raise_for_status
                if response.status_code == 401 or response.status_code >= 500:
                    if attempt < JWT_MINT_RETRIES - 1:
                        delay = exponential_backoff_with_jitter(attempt, base_delay=2.0, max_delay=10.0)
                        print(
                            f"[Dominus] JWT mint returned {response.status_code}, "
                            f"retrying in {delay:.1f}s (attempt {attempt + 1}/{JWT_MINT_RETRIES})"
                        )
                        await asyncio.sleep(delay)
                        continue

                response.raise_for_status()

                # Decode base64 response
                result = _b64_decode(response.text)

                if not result.get("success"):
                    error_msg = result.get("error", "Unknown auth error")
                    sovereign_circuit_breaker.record_failure()
                    raise RuntimeError(f"Auth error: {error_msg}")

                data = result.get("data", {})
                jwt = data.get("access_token") or data.get("token")
                if not jwt:
                    sovereign_circuit_breaker.record_failure()
                    raise RuntimeError("No JWT token in auth response")

                # Success - record it
                sovereign_circuit_breaker.record_success()
                return jwt

        except httpx.TimeoutException as e:
            last_error = e
            if attempt < JWT_MINT_RETRIES - 1:
                delay = exponential_backoff_with_jitter(attempt, base_delay=2.0, max_delay=10.0)
                print(
                    f"[Dominus] JWT mint timed out, "
                    f"retrying in {delay:.1f}s (attempt {attempt + 1}/{JWT_MINT_RETRIES})"
                )
                await asyncio.sleep(delay)
                continue
            sovereign_circuit_breaker.record_failure()
            raise RuntimeError(f"Failed to get JWT: {e}") from e

        except httpx.NetworkError as e:
            last_error = e
            if attempt < JWT_MINT_RETRIES - 1:
                delay = exponential_backoff_with_jitter(attempt, base_delay=2.0, max_delay=10.0)
                print(
                    f"[Dominus] JWT mint network error ({e}), "
                    f"retrying in {delay:.1f}s (attempt {attempt + 1}/{JWT_MINT_RETRIES})"
                )
                await asyncio.sleep(delay)
                continue
            sovereign_circuit_breaker.record_failure()
            raise RuntimeError(f"Failed to get JWT: {e}") from e

        except httpx.HTTPStatusError as e:
            last_error = e
            # 4xx errors (except 401 which is retried above) should not be retried
            if 400 <= e.response.status_code < 500 and e.response.status_code != 401:
                sovereign_circuit_breaker.record_failure()
                raise RuntimeError(f"Failed to get JWT: {e}") from e
            # For other errors, we've already handled retries in the status check above
            sovereign_circuit_breaker.record_failure()
            raise RuntimeError(f"Failed to get JWT: {e}") from e

    # Should not reach here, but just in case
    sovereign_circuit_breaker.record_failure()
    raise RuntimeError(f"Failed to get JWT after {JWT_MINT_RETRIES} retries: {last_error}")


def _get_architect_url(psk_token: str = None, sovereign_url: str = None, environment: str = None) -> str:
    """
    Get Architect Cloud URL from SDK config.

    Uses flat file config (dominus/config/endpoints.py) for URL lookup.
    No network calls needed - URLs are hardcoded constants.

    Args:
        psk_token: Unused (kept for backward compatibility)
        sovereign_url: Unused (kept for backward compatibility)
        environment: Environment override (development, staging, production).
                     Defaults to CB_ENVIRONMENT env var or "production".

    Returns:
        Architect base URL string
    """
    from ..config.endpoints import get_architect_url
    return get_architect_url(environment)


async def _ensure_valid_jwt(psk_token: str, sovereign_url: str) -> str:
    """
    Ensure we have a valid JWT, fetching and caching if needed.
    
    Cache key: "jwt:self:service"
    Cache TTL: 14 minutes (JWT lifetime is 15 minutes)
    Refresh when <60 seconds remain.
    
    Args:
        psk_token: PSK token (DOMINUS_TOKEN)
        sovereign_url: Sovereign base URL
        
    Returns:
        Valid JWT token string
    """
    cache_key = "jwt:self:service"
    
    # Check cache
    cached_jwt = dominus_cache.get(cache_key)
    if cached_jwt:
        try:
            # Decode payload to check expiry
            payload = _decode_jwt_payload(cached_jwt)
            exp = payload.get("exp", 0)
            current_time = int(time.time())
            
            # Refresh if <60 seconds remain
            if exp - current_time > 60:
                return cached_jwt
        except Exception:
            # If decode fails, fetch new JWT
            pass
    
    # Fetch new JWT
    jwt = await _get_service_jwt(psk_token, sovereign_url)
    
    # Cache for 14 minutes (840 seconds)
    dominus_cache.set(cache_key, jwt, ttl=840)
    
    return jwt


def verify_token_format(token: str) -> bool:
    """
    Verify token format is valid (basic check, not server verification).
    Actual token validation happens when we call /api/warden/mint.

    Args:
        token: Auth token to verify

    Returns:
        True if token format is valid

    Raises:
        RuntimeError: If token format is invalid
    """
    # PSK tokens are 64-character hex strings
    if not token or len(token) < 32:
        raise RuntimeError("Invalid token format")
    return True


async def health_check_all(base_url: str) -> dict:
    """
    Check health of orchestrator services.

    Args:
        base_url: Orchestrator base URL

    Returns:
        Health status dict with service results
    """
    results = {}

    # Check orchestrator via /api/health
    try:
        start = time.time()
        async with httpx.AsyncClient(base_url=base_url, timeout=5.0) as client:
            response = await client.get("/api/health")
            response.raise_for_status()

            # Parse response (may be JSON string or dict)
            health_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {"status": "ok"}

        latency = int((time.time() - start) * 1000)
        results["orchestrator"] = {
            "status": health_data.get("status", "healthy"),
            "latency_ms": latency,
            **health_data
        }
    except Exception as e:
        results["orchestrator"] = {"status": "unhealthy", "error": str(e)}
        return {"status": "unhealthy", "services": results, "message": "Orchestrator unhealthy"}

    return {"status": "healthy", "services": results, "message": "All services healthy"}


async def get_service_url(service_name: str, token: str, sovereign_url: str) -> str:
    """
    Get service base URL. Cache-first, then asks sovereign.
    
    Args:
        service_name: "architect", "notifier", etc.
        token: Auth token (for sovereign API call)
        sovereign_url: Sovereign base URL
        
    Returns:
        Base URL for the service
    """
    cache_key = f"service_url:{service_name}"
    
    # Check cache first
    cached = dominus_cache.get(cache_key)
    if cached:
        return cached
    
    # Ask sovereign (future endpoint)
    # TODO: Create endpoint in sovereign to return service URLs
    # For now, construct from pattern
    url = f"https://{service_name}-cloud-production-775398158805.us-east4.run.app"
    
    # Cache with long TTL (URLs don't change often)
    dominus_cache.set(cache_key, url, ttl=3600)  # 1 hour
    
    return url


async def execute_with_retry(
    route_info: tuple[str, str, bool, bool],
    base_url: str,
    token: str | None,
    kwargs: dict
) -> DominusResponse:
    """
    Execute HTTP request with retry logic.
    
    Args:
        route_info: (method, path, requires_auth, cacheable)
        base_url: Base URL for API
        token: Auth token (if needed)
        kwargs: Request parameters
        
    Returns:
        Response dict
    """
    method, path, requires_auth, cacheable = route_info
    
    # Check cache first
    if cacheable and kwargs:
        cache_key = f"{path}:{str(sorted(kwargs.items()))}"
        cached = dominus_cache.get(cache_key)
        if cached:
            return cached
    
    # Validate token
    if requires_auth and not token:
        raise RuntimeError(
            "DOMINUS_TOKEN not set. "
            "Set the environment variable: export DOMINUS_TOKEN=your_token"
        )
    
    # Retry loop with exponential backoff and jitter
    for attempt in range(MAX_RETRIES):
        try:
            # Prepare headers
            headers = {}
            if requires_auth:
                headers["Authorization"] = f"Bearer {_b64_token(token)}"
            
            # Prepare body (encode if auth required and kwargs provided)
            # For auth routes: send raw base64 string as text/plain (matches middleware expectation)
            # For non-auth routes: send JSON as normal
            if requires_auth and kwargs:
                body_b64 = _b64_encode(kwargs)
                headers["Content-Type"] = "text/plain"
                body = body_b64
            else:
                body = kwargs if kwargs else {}
            
            # Make request
            async with httpx.AsyncClient(base_url=base_url, headers=headers, timeout=30.0) as client:
                if method == "GET":
                    response = await client.get(path, params=kwargs if kwargs else None)
                else:
                    if requires_auth and kwargs:
                        # Send raw base64 string as text
                        response = await client.post(path, content=body)
                    else:
                        # Send JSON as normal
                        response = await client.post(path, json=body if body else {})
            
            response.raise_for_status()
            
            # Decode response
            # For auth routes: middleware returns raw base64 string as text/plain
            # For non-auth routes: normal JSON response
            if requires_auth:
                # Read response as text (base64 string), then decode
                result = _b64_decode(response.text)
            else:
                result = response.json()
            
            # Cache if needed (encrypted automatically)
            if cacheable and kwargs:
                dominus_cache.set(cache_key, result, ttl=300)
            
            return result
        
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            if attempt == MAX_RETRIES - 1:  # Last attempt
                raise RuntimeError(f"Request failed after {MAX_RETRIES} retries: {e}") from e
            delay = exponential_backoff_with_jitter(attempt, base_delay=1.0, max_delay=15.0)
            await asyncio.sleep(delay)
        
        except httpx.HTTPStatusError as e:
            # Don't retry 4xx errors (client errors)
            if 400 <= e.response.status_code < 500:
                # Try to decode error response for better error messages
                error_detail = f"HTTP {e.response.status_code}"
                try:
                    if requires_auth:
                        # Auth routes return base64-encoded responses
                        error_body = _b64_decode(e.response.text)
                        if isinstance(error_body, dict):
                            error_detail = error_body.get("error") or error_body.get("detail") or str(error_body)
                        else:
                            error_detail = str(error_body)
                    else:
                        # Non-auth routes return JSON
                        error_body = e.response.json()
                        error_detail = error_body.get("error") or error_body.get("detail") or str(error_body)
                except Exception:
                    # If decoding fails, use response text as-is
                    error_detail = e.response.text[:200] if e.response.text else str(e)

                raise RuntimeError(f"{error_detail} (status {e.response.status_code})") from e
            if attempt == 2:  # Last attempt
                raise
            await asyncio.sleep(2 ** attempt)


async def execute_bridge_call(
    method: str,
    base_url: str,
    token: str,
    params: dict,
    cacheable: bool = False,
    endpoint: str = "/newapi/bridge"
) -> DominusResponse:
    """
    Execute a call to the Bridge API (or crossover endpoint).

    The Bridge API uses:
    - JWT token in Authorization header (obtained via _ensure_valid_jwt)
    - Base64-encoded JSON body: {"method": "...", "params": {...}}
    - Base64-encoded JSON response: {"success": true, "data": {...}}

    Args:
        method: Bridge method name (e.g., "secrets.get")
        base_url: Base URL for sovereign
        token: PSK token (used to get JWT via _ensure_valid_jwt)
        params: Method parameters
        cacheable: Whether to cache the result
        endpoint: API endpoint path (default: "/newapi/bridge", can be "/newapi/crossover")

    Returns:
        Response data (the "data" field from successful response)
    """
    # Check cache first
    if cacheable and params:
        cache_key = f"bridge:{method}:{str(sorted(params.items()))}"
        cached = dominus_cache.get(cache_key)
        if cached:
            return cached

    if not token:
        raise RuntimeError(
            "DOMINUS_TOKEN not set. "
            "Set the environment variable: export DOMINUS_TOKEN=your_token"
        )

    # Get JWT for Bridge/Crossover calls
    jwt = await _ensure_valid_jwt(token, base_url)

    # Prepare Bridge API request with JWT
    headers = {
        "Authorization": f"Bearer {jwt}",
        "Content-Type": "text/plain"
    }

    # Body format: {"method": "...", "params": {...}}
    body_json = {"method": method, "params": params}
    body_b64 = _b64_encode(body_json)

    # Retry loop with exponential backoff and jitter
    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(base_url=base_url, headers=headers, timeout=30.0) as client:
                response = await client.post(endpoint, content=body_b64)

            response.raise_for_status()

            # Decode base64 response
            result = _b64_decode(response.text)

            # Bridge API returns {"success": true, "data": {...}} or {"success": false, "error": "..."}
            if not result.get("success"):
                error_msg = result.get("error", "Unknown bridge error")
                raise RuntimeError(f"Bridge error: {error_msg}")

            data = result.get("data", {})

            # Cache if needed
            if cacheable and params:
                dominus_cache.set(cache_key, data, ttl=300)

            return data

        except (httpx.TimeoutException, httpx.NetworkError) as e:
            if attempt == MAX_RETRIES - 1:
                raise RuntimeError(f"Bridge call failed after {MAX_RETRIES} retries: {e}") from e
            delay = exponential_backoff_with_jitter(attempt, base_delay=1.0, max_delay=15.0)
            await asyncio.sleep(delay)

        except httpx.HTTPStatusError as e:
            # Don't retry 4xx errors
            if 400 <= e.response.status_code < 500:
                error_detail = f"HTTP {e.response.status_code}"
                try:
                    error_body = _b64_decode(e.response.text)
                    if isinstance(error_body, dict):
                        error_detail = error_body.get("error") or str(error_body)
                    else:
                        error_detail = str(error_body)
                except Exception:
                    error_detail = e.response.text[:200] if e.response.text else str(e)

                raise RuntimeError(f"{error_detail} (status {e.response.status_code})") from e
            if attempt == MAX_RETRIES - 1:
                raise RuntimeError(f"Bridge call failed after {MAX_RETRIES} retries: {e}") from e
            delay = exponential_backoff_with_jitter(attempt, base_delay=1.0, max_delay=15.0)
            await asyncio.sleep(delay)


async def execute_command(command: str, token: str, sovereign_url: str, **kwargs) -> DominusResponse:
    """
    Execute a command by routing to the appropriate service handler.
    
    Args:
        command: Command string (e.g., "secrets.get", "health.check", "auth.self")
        token: PSK auth token (DOMINUS_TOKEN)
        sovereign_url: Sovereign base URL
        **kwargs: Command parameters
        
    Returns:
        Response dict
    """
    # Special command: health.check
    if command == "health.check":
        return await health_check_all(sovereign_url)
    
    # Special command: auth.self (get service JWT)
    if command == "auth.self":
        jwt = await _ensure_valid_jwt(token, sovereign_url)
        return {"access_token": jwt, "token_type": "bearer"}
    
    # Route Sovereign auth commands to /newapi/auth
    # auth.jwks is public (no PSK required), auth.mint requires PSK
    if command == "auth.jwks":
        return await _execute_auth_call(command, None, sovereign_url, **kwargs)
    elif command == "auth.mint":
        return await _execute_auth_call(command, token, sovereign_url, **kwargs)

    # Route sql.* commands to Architect
    if command.startswith("sql."):
        from ..services import architect
        architect_url = _get_architect_url(token, sovereign_url)
        return await architect.handle(command, token, architect_url, sovereign_url, **kwargs)

    # Route auth.* commands to Architect (subsidiary auth management)
    # Note: auth.jwks and auth.mint are handled above (Sovereign)
    if command.startswith("auth."):
        from ..services import architect
        architect_url = _get_architect_url(token, sovereign_url)
        return await architect.handle(command, token, architect_url, sovereign_url, **kwargs)

    # Route schema.* commands to Architect
    if command.startswith("schema."):
        from ..services import architect
        architect_url = _get_architect_url(token, sovereign_url)
        return await architect.handle(command, token, architect_url, sovereign_url, **kwargs)

    # Route crossover.sql.* to Architect Crossover
    if command.startswith("crossover.sql."):
        from ..services import architect
        architect_url = _get_architect_url(token, sovereign_url)
        return await architect.handle(command, token, architect_url, sovereign_url, **kwargs)
    
    # Route crossover.* (non-sql) to Sovereign Crossover
    if command.startswith("crossover."):
        from ..services import sovereign
        return await sovereign.handle(command, token, sovereign_url, **kwargs)
    
    # Default to Sovereign
    from ..services import sovereign
    return await sovereign.handle(command, token, sovereign_url, **kwargs)


async def _execute_auth_call(
    method: str,
    psk_token: Optional[str],
    base_url: str,
    **kwargs
) -> DominusResponse:
    """
    Execute an auth call to /api/warden/* endpoints.

    Args:
        method: Auth method name (e.g., "auth.mint", "auth.jwks")
        psk_token: PSK token (DOMINUS_TOKEN) - None for public endpoints like auth.jwks
        base_url: Orchestrator base URL
        **kwargs: Method parameters

    Returns:
        Response data
    """
    headers = {
        "Content-Type": "text/plain"
    }

    # Add PSK header only if token provided (auth.jwks is public)
    if psk_token:
        headers["Authorization"] = f"Bearer {psk_token}"

    # Body format: {"method": "...", "params": {...}}
    body_json = {"method": method, "params": kwargs}
    body_b64 = _b64_encode(body_json)

    # Map method to endpoint
    if method == "auth.jwks":
        endpoint = "/api/warden/jwks"
    elif method == "auth.mint":
        endpoint = "/api/warden/mint"
    else:
        endpoint = "/api/warden/mint"

    async with httpx.AsyncClient(base_url=base_url, headers=headers, timeout=30.0) as client:
        response = await client.post(endpoint, content=body_b64)
        response.raise_for_status()

        # Decode base64 response
        result = _b64_decode(response.text)

        if not result.get("success"):
            error_msg = result.get("error", "Unknown auth error")
            raise RuntimeError(f"Auth error: {error_msg}")

        return result.get("data", {})

