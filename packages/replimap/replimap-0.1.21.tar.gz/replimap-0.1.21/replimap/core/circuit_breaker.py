"""
Circuit Breaker for AWS API Resilience.

This module implements the Circuit Breaker pattern to prevent
cascading failures when AWS services or regions are unavailable.

The circuit breaker has three states:
- CLOSED: Normal operation, requests pass through
- OPEN: Service is failing, requests fail-fast without calling AWS
- HALF_OPEN: Testing if service has recovered

This prevents:
- Infinite retry loops on service outages
- User waiting forever for unavailable regions
- Wasted API quota on failing services
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, skip calls
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitOpenError(Exception):
    """Raised when the circuit breaker is open and blocking calls."""

    def __init__(self, message: str, circuit_key: str | None = None) -> None:
        super().__init__(message)
        self.circuit_key = circuit_key


@dataclass
class CircuitBreaker:
    """
    Circuit breaker for resilient AWS API calls.

    Usage:
        circuit = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

        try:
            result = await circuit.call(async_function, arg1, arg2)
        except CircuitOpenError:
            # Service is unavailable, skip this region/service
            pass
        except SomeAWSError:
            # Handle the actual error
            pass

    Attributes:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before testing recovery
        key: Optional identifier for this circuit (e.g., "us-east-1/ec2")
    """

    failure_threshold: int = 3
    recovery_timeout: float = 60.0
    key: str | None = None

    # Internal state
    _failure_count: int = field(default=0, init=False)
    _last_failure_time: float | None = field(default=None, init=False)
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _success_count_in_half_open: int = field(default=0, init=False)
    # Thread safety: Lock protects all state mutations
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    @property
    def state(self) -> CircuitState:
        """Get the current circuit state, checking for recovery. Thread-safe."""
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._should_attempt_recovery():
                    self._state = CircuitState.HALF_OPEN
                    self._success_count_in_half_open = 0
                    logger.info(
                        f"Circuit breaker {self.key or 'default'} entering HALF_OPEN state"
                    )
            return self._state

    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self._last_failure_time is None:
            return True
        return time.time() - self._last_failure_time >= self.recovery_timeout

    def call(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        """
        Call a function through the circuit breaker (sync version).

        Args:
            func: The function to call
            *args: Positional arguments to pass to func
            **kwargs: Keyword arguments to pass to func

        Returns:
            Result from the function

        Raises:
            CircuitOpenError: If circuit is open and blocking calls
        """
        current_state = self.state

        if current_state == CircuitState.OPEN:
            raise CircuitOpenError(
                f"Circuit breaker is OPEN for {self.key or 'service'}. "
                f"Skipping to prevent cascading failures.",
                circuit_key=self.key,
            )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise

    async def async_call(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        """
        Call an async function through the circuit breaker.

        Args:
            func: The async function to call
            *args: Positional arguments to pass to func
            **kwargs: Keyword arguments to pass to func

        Returns:
            Result from the function

        Raises:
            CircuitOpenError: If circuit is open and blocking calls
        """
        current_state = self.state

        if current_state == CircuitState.OPEN:
            raise CircuitOpenError(
                f"Circuit breaker is OPEN for {self.key or 'service'}. "
                f"Skipping to prevent cascading failures.",
                circuit_key=self.key,
            )

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise

    def _on_success(self) -> None:
        """Handle successful call. Thread-safe."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count_in_half_open += 1
                # Require 2 successful calls before fully closing
                if self._success_count_in_half_open >= 2:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    logger.info(
                        f"Circuit breaker {self.key or 'default'} CLOSED after recovery"
                    )
            else:
                # In closed state, reset failure count on success
                self._failure_count = 0

    def _on_failure(self, error: Exception) -> None:
        """Handle failed call. Thread-safe."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Failed during recovery test, go back to OPEN
                self._state = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker {self.key or 'default'} back to OPEN "
                    f"after failed recovery test: {error}"
                )
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker {self.key or 'default'} OPEN after "
                    f"{self._failure_count} failures. Will retry in {self.recovery_timeout}s"
                )

    def reset(self) -> None:
        """Manually reset the circuit breaker to closed state. Thread-safe."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None
            self._success_count_in_half_open = 0

    def force_open(self) -> None:
        """Manually force the circuit breaker to open state. Thread-safe."""
        with self._lock:
            self._state = CircuitState.OPEN
            self._last_failure_time = time.time()


class CircuitBreakerRegistry:
    """
    Registry for circuit breakers by region/service.

    Allows shared circuit breaker state across scanners for the same
    region or service. Thread-safe for concurrent scanner access.
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0,
    ) -> None:
        """
        Initialize the registry.

        Args:
            failure_threshold: Default failure threshold for new circuits
            recovery_timeout: Default recovery timeout for new circuits
        """
        self._lock = threading.Lock()
        self._circuits: dict[str, CircuitBreaker] = {}
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout

    def get(self, key: str) -> CircuitBreaker:
        """
        Get or create a circuit breaker for a key. Thread-safe.

        Uses double-checked locking for performance: fast path without
        lock when circuit already exists.

        Args:
            key: Identifier like "us-east-1" or "us-east-1/ec2"

        Returns:
            CircuitBreaker instance for this key
        """
        # Fast path: circuit already exists (no lock needed for read)
        if key in self._circuits:
            return self._circuits[key]

        # Slow path: need to create circuit (requires lock)
        with self._lock:
            # Double-check after acquiring lock
            if key not in self._circuits:
                self._circuits[key] = CircuitBreaker(
                    failure_threshold=self._failure_threshold,
                    recovery_timeout=self._recovery_timeout,
                    key=key,
                )
            return self._circuits[key]

    def get_for_region_service(self, region: str, service: str) -> CircuitBreaker:
        """
        Get or create a circuit breaker for a region/service combination.

        Args:
            region: AWS region (e.g., "us-east-1")
            service: AWS service (e.g., "ec2")

        Returns:
            CircuitBreaker instance
        """
        key = f"{region}/{service}"
        return self.get(key)

    def get_open_circuits(self) -> list[str]:
        """Get list of currently open circuit keys."""
        return [
            key for key, cb in self._circuits.items() if cb.state == CircuitState.OPEN
        ]

    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        for cb in self._circuits.values():
            cb.reset()

    def stats(self) -> dict[str, Any]:
        """Get statistics about all circuit breakers."""
        return {
            "total_circuits": len(self._circuits),
            "open_circuits": self.get_open_circuits(),
            "circuits": {
                key: {
                    "state": cb.state.value,
                    "failure_count": cb._failure_count,
                }
                for key, cb in self._circuits.items()
            },
        }


# Global registry instance for shared state
_global_registry: CircuitBreakerRegistry | None = None


def get_circuit_breaker_registry(
    failure_threshold: int = 3,
    recovery_timeout: float = 60.0,
) -> CircuitBreakerRegistry:
    """
    Get the global circuit breaker registry.

    Args:
        failure_threshold: Default failure threshold for new circuits
        recovery_timeout: Default recovery timeout for new circuits

    Returns:
        Global CircuitBreakerRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = CircuitBreakerRegistry(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )
    return _global_registry
