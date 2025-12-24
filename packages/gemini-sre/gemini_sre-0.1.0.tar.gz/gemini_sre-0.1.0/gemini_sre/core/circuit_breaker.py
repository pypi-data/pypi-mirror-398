"""
Circuit breaker implementation for multi-region failover.

Prevents wasting time and quota on failing regions by intelligently
tracking region health and automatically skipping unhealthy regions.
"""

import logging
import time
from enum import Enum
from typing import Any, Callable, Optional


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"  # Region is failing, skip it
    HALF_OPEN = "HALF_OPEN"  # Testing if region recovered


class CircuitBreaker:
    """
    Circuit breaker for multi-region failover.

    Prevents wasting time and quota on failing regions by:
    - Opening circuit after threshold failures
    - Skipping failed regions automatically
    - Testing recovery after timeout
    - Auto-closing when region recovers

    States:
    - CLOSED: Normal operation, all requests allowed
    - OPEN: Region failing, reject all requests
    - HALF_OPEN: Testing recovery, allow limited requests
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: int = 60,
        window: int = 120,
        logger: Optional[logging.Logger] = None,
        on_state_change: Optional[Callable[[str, CircuitState, CircuitState], None]] = None,
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Open circuit after N failures in window
            success_threshold: Close circuit after N successes in HALF_OPEN
            timeout: Seconds before trying failed region again
            window: Time window (seconds) for counting failures
            logger: Optional logger for circuit state changes
            on_state_change: Optional callback function called on state transitions
                            Signature: func(region: str, old_state: CircuitState, new_state: CircuitState)
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.window = window
        self.logger = logger
        self.on_state_change = on_state_change

        # Per-region state tracking
        self.state: dict[str, CircuitState] = {}
        self.failure_count: dict[str, int] = {}
        self.success_count: dict[str, int] = {}
        self.failure_timestamps: dict[str, list[float]] = {}
        self.opened_at: dict[str, float] = {}

    def is_available(self, region: str) -> bool:
        """
        Check if region is available for requests.

        Args:
            region: GCP region name

        Returns:
            True if region can handle requests, False otherwise
        """
        current_state = self.state.get(region, CircuitState.CLOSED)

        if current_state == CircuitState.CLOSED:
            return True

        if current_state == CircuitState.OPEN:
            # Check if timeout expired → transition to HALF_OPEN
            if time.time() - self.opened_at[region] >= self.timeout:
                self._transition_state(region, CircuitState.HALF_OPEN)
                self.success_count[region] = 0
                return True  # Allow test request
            return False  # Still open, reject

        if current_state == CircuitState.HALF_OPEN:
            return True  # Allow test requests

        return False

    def record_success(self, region: str):
        """
        Record successful request.

        Args:
            region: GCP region name
        """
        current_state = self.state.get(region, CircuitState.CLOSED)

        if current_state == CircuitState.HALF_OPEN:
            self.success_count[region] = self.success_count.get(region, 0) + 1

            # Enough successes → CLOSE circuit
            if self.success_count[region] >= self.success_threshold:
                self._transition_state(region, CircuitState.CLOSED)
                self.failure_count[region] = 0
                self.failure_timestamps[region] = []

        # Reset failures on success in CLOSED state
        if current_state == CircuitState.CLOSED:
            self.failure_count[region] = 0
            self.failure_timestamps[region] = []

    def record_failure(self, region: str, error: Optional[Exception] = None):
        """
        Record failed request and potentially open circuit.

        Args:
            region: GCP region name
            error: Optional exception that caused failure
        """
        current_time = time.time()

        # Initialize if needed
        if region not in self.failure_timestamps:
            self.failure_timestamps[region] = []

        # Remove old failures outside window
        self.failure_timestamps[region] = [
            ts for ts in self.failure_timestamps[region] if current_time - ts <= self.window
        ]

        # Add new failure
        self.failure_timestamps[region].append(current_time)
        self.failure_count[region] = len(self.failure_timestamps[region])

        current_state = self.state.get(region, CircuitState.CLOSED)

        # CLOSED → OPEN if threshold exceeded
        if current_state == CircuitState.CLOSED:
            if self.failure_count[region] >= self.failure_threshold:
                self.opened_at[region] = current_time
                self._transition_state(region, CircuitState.OPEN)

        # HALF_OPEN → OPEN if test failed
        elif current_state == CircuitState.HALF_OPEN:
            self.opened_at[region] = current_time
            self.success_count[region] = 0
            self._transition_state(region, CircuitState.OPEN)

    def get_available_regions(self, all_regions: list[str]) -> list[str]:
        """
        Get list of regions with available circuits.

        Args:
            all_regions: All configured regions

        Returns:
            List of regions that can handle requests
        """
        return [region for region in all_regions if self.is_available(region)]

    def get_state(self, region: str) -> CircuitState:
        """Get current circuit state for a region."""
        return self.state.get(region, CircuitState.CLOSED)

    def get_stats(self) -> dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "states": {region: state.value for region, state in self.state.items()},
            "failure_counts": self.failure_count.copy(),
            "open_circuits": [r for r, s in self.state.items() if s == CircuitState.OPEN],
        }

    def _transition_state(self, region: str, new_state: CircuitState):
        """Transition circuit to new state with logging and callback."""
        old_state = self.state.get(region, CircuitState.CLOSED)
        self.state[region] = new_state

        if old_state != new_state:
            # Log state change
            if self.logger:
                emoji = {"OPEN": "🔴", "CLOSED": "✅", "HALF_OPEN": "🟡"}
                self.logger.info(
                    f"{emoji.get(new_state.value, '⚪')} Circuit breaker {region}: "
                    f"{old_state.value} → {new_state.value}"
                )

            # Call state change callback
            if self.on_state_change:
                self.on_state_change(region, old_state, new_state)
