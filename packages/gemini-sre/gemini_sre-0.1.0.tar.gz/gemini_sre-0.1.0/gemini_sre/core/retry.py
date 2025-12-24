"""
Retry configuration management.

Provides default retry configurations for different operation types.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class RetryConfig:
    """
    Retry configuration manager.

    Provides type-specific retry configurations for different API operations.
    """

    max_retries: int = 5
    initial_delay: float = 1.0
    max_delay: float = 16.0
    exp_base: float = 2.0
    jitter: float = 0.5
    custom_config: Optional[dict[str, Any]] = field(default=None)

    # Default retry configurations by operation type
    DEFAULT_CONFIGS: dict[str, dict[str, Any]] = field(
        default_factory=lambda: {
            "idempotent_read": {
                "max_retries": 5,
                "initial_delay": 1.0,
                "max_delay": 16.0,
                "exp_base": 2.0,
                "jitter": 0.5,
            },
            "idempotent_write": {
                "max_retries": 3,
                "initial_delay": 1.0,
                "max_delay": 16.0,
                "exp_base": 2.0,
                "jitter": 0.5,
            },
            "non_idempotent": {
                "max_retries": 0,  # No retry for non-idempotent ops
                "initial_delay": 0.0,
                "max_delay": 0.0,
                "exp_base": 1.0,
                "jitter": 0.0,
            },
            "expensive_idempotent": {
                "max_retries": 2,  # Limited retries for expensive ops
                "initial_delay": 2.0,
                "max_delay": 32.0,
                "exp_base": 2.0,
                "jitter": 0.5,
            },
            "streaming": {
                "max_retries": 3,
                "initial_delay": 1.0,
                "max_delay": 8.0,
                "exp_base": 2.0,
                "jitter": 0.3,
            },
            "stateful": {
                "max_retries": 1,  # Very limited retry for stateful ops
                "initial_delay": 1.0,
                "max_delay": 4.0,
                "exp_base": 2.0,
                "jitter": 0.5,
            },
            "streaming_stateful": {
                "max_retries": 0,  # No automatic retry
                "initial_delay": 0.0,
                "max_delay": 0.0,
                "exp_base": 1.0,
                "jitter": 0.0,
            },
        }
    )

    def get_config(self, operation_type: str) -> dict[str, Any]:
        """
        Get retry config for specific operation type.

        Args:
            operation_type: Type of operation (idempotent_read, streaming, etc.)

        Returns:
            Retry configuration dict
        """
        # Check custom config first
        if self.custom_config and operation_type in self.custom_config:
            return self.custom_config[operation_type]

        # Use default config
        if operation_type in self.DEFAULT_CONFIGS:
            return self.DEFAULT_CONFIGS[operation_type]

        # Fallback to instance defaults
        return {
            "max_retries": self.max_retries,
            "initial_delay": self.initial_delay,
            "max_delay": self.max_delay,
            "exp_base": self.exp_base,
            "jitter": self.jitter,
        }
