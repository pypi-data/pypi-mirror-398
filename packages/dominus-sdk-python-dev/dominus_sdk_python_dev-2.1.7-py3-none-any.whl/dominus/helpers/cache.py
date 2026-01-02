"""
Internal cache with automatic encryption and circuit breaker.

NOT exposed to SDK users - internal use only.
"""
import time
import json
import base64
import random
from typing import Dict, Tuple, Optional, Any
from cryptography.fernet import Fernet
from hashlib import sha256


class CircuitBreaker:
    """
    Simple circuit breaker to prevent runaway retries.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests blocked
    - HALF_OPEN: Testing if service recovered

    Prevents CPU/quota exhaustion from retry storms.
    """

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 1
    ):
        self._failure_count = 0
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._half_open_max_calls = half_open_max_calls
        self._state = self.CLOSED
        self._last_failure_time: float = 0
        self._half_open_calls = 0

    @property
    def state(self) -> str:
        """Get current state, transitioning OPEN→HALF_OPEN if timeout elapsed."""
        if self._state == self.OPEN:
            if time.time() - self._last_failure_time >= self._recovery_timeout:
                self._state = self.HALF_OPEN
                self._half_open_calls = 0
        return self._state

    def can_execute(self) -> bool:
        """Check if a request can be executed."""
        state = self.state
        if state == self.CLOSED:
            return True
        if state == self.HALF_OPEN:
            return self._half_open_calls < self._half_open_max_calls
        return False  # OPEN

    def record_success(self) -> None:
        """Record a successful call."""
        if self._state == self.HALF_OPEN:
            self._state = self.CLOSED
        self._failure_count = 0
        self._half_open_calls = 0

    def record_failure(self) -> None:
        """Record a failed call."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == self.HALF_OPEN:
            # Failed during recovery test, go back to OPEN
            self._state = self.OPEN
        elif self._failure_count >= self._failure_threshold:
            self._state = self.OPEN

    def record_half_open_call(self) -> None:
        """Record a call attempt in HALF_OPEN state."""
        self._half_open_calls += 1


def exponential_backoff_with_jitter(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    jitter: float = 0.5
) -> float:
    """
    Calculate backoff delay with jitter to prevent thundering herd.

    Args:
        attempt: Zero-based attempt number
        base_delay: Base delay in seconds
        max_delay: Maximum delay cap
        jitter: Jitter factor (0-1), adds randomness

    Returns:
        Delay in seconds
    """
    delay = min(base_delay * (2 ** attempt), max_delay)
    jitter_range = delay * jitter
    return delay + random.uniform(-jitter_range, jitter_range)


class DominusCache:
    """
    Internal process-local cache with auto-encryption.

    Used by dominus services only:
    - Validation state
    - Service URLs
    - API responses

    NOT accessible by SDK users.
    """

    def __init__(self, default_ttl: int = 300):
        self._store: Dict[str, Tuple[bytes, float]] = {}
        self._default_ttl = default_ttl
        self._cipher: Optional[Fernet] = None

    def set_encryption_key(self, token: str) -> None:
        """Initialize encryption using auth token."""
        if not token:
            return
        key = base64.urlsafe_b64encode(sha256(token.encode()).digest())
        self._cipher = Fernet(key)

    def get(self, key: str) -> Optional[Any]:
        """Get and decrypt, refresh TTL."""
        entry = self._store.get(key)
        if not entry:
            return None

        encrypted_value, expires_at = entry

        # Check expiry
        if time.time() >= expires_at:
            del self._store[key]
            return None

        # Decrypt
        if self._cipher:
            try:
                decrypted = self._cipher.decrypt(encrypted_value)
                value = json.loads(decrypted.decode())
            except Exception:
                del self._store[key]
                return None
        else:
            value = json.loads(encrypted_value.decode())

        # Touch TTL
        self._store[key] = (encrypted_value, time.time() + self._default_ttl)
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Encrypt and store."""
        duration = ttl if ttl is not None else self._default_ttl

        if self._cipher:
            plaintext = json.dumps(value).encode()
            encrypted_value = self._cipher.encrypt(plaintext)
        else:
            encrypted_value = json.dumps(value).encode()

        self._store[key] = (encrypted_value, time.time() + duration)

    def delete(self, key: str) -> bool:
        """Delete key."""
        return bool(self._store.pop(key, None))

    def clear(self) -> int:
        """Clear all."""
        count = len(self._store)
        self._store.clear()
        return count


# Internal singletons - NOT exported to users
dominus_cache = DominusCache(default_ttl=300)

# Circuit breakers for different services (prevents retry storms)
sovereign_circuit_breaker = CircuitBreaker(
    failure_threshold=5,    # Open after 5 consecutive failures
    recovery_timeout=30.0,  # Try again after 30 seconds
    half_open_max_calls=1   # Allow 1 test call in half-open state
)
