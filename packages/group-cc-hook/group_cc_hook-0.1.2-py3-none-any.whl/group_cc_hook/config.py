"""
Configuration module - Provides configurable parameters

Usage example:
    from config import HookConfig

    config = HookConfig(
        timeout_seconds=600,  # 10-minute timeout
        check_interval_ms=5,  # 5ms check interval
    )
    run_daemon(config)
"""

import os
from dataclasses import dataclass


def _parse_bool_env(value: str) -> bool:
    """Parse boolean environment variable value"""
    return value.lower() in ("1", "true", "yes", "on")

@dataclass
class HookConfig:
    """
    Hook monitoring configuration

    Attributes:
        timeout_seconds: Timeout in seconds, default 300 (5 minutes)
        check_interval_ms: Check interval in milliseconds, default 1ms
        signal_number: Signal number to send on timeout, default SIGUSR1 (10)
        send_signal_on_timeout: Send signal on timeout, default True
    """

    timeout_seconds: int = 300  # 5 minutes
    check_interval_ms: int = 1
    signal_number: int = 10  # SIGUSR1
    send_signal_on_timeout: bool = True  # Default: send signal for notification

    def __post_init__(self):
        """Validate configuration parameters"""
        if self.timeout_seconds <= 0:
            raise ValueError(
                f"timeout_seconds must be positive, got {self.timeout_seconds}"
            )

        if self.check_interval_ms <= 0:
            raise ValueError(
                f"check_interval_ms must be positive, got {self.check_interval_ms}"
            )

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "timeout_seconds": self.timeout_seconds,
            "check_interval_ms": self.check_interval_ms,
            "signal_number": self.signal_number,
            "send_signal_on_timeout": self.send_signal_on_timeout,
        }

    @classmethod
    def from_dict(cls, config_dict):
        """Create configuration from dictionary"""
        return cls(**{k: v for k, v in config_dict.items() if k in cls.__annotations__})

    @classmethod
    def from_env(cls):
        """Create configuration from environment variables"""
        return cls(
            timeout_seconds=int(os.environ.get("PG_HOOK_TIMEOUT", 300)),
            check_interval_ms=int(os.environ.get("PG_HOOK_CHECK_INTERVAL", 10)),
            signal_number=int(os.environ.get("PG_HOOK_SIGNAL", 10)),
            send_signal_on_timeout=_parse_bool_env(
                os.environ.get("PG_HOOK_SEND_SIGNAL", "1")
            ),
        )


# Default configuration instance
DEFAULT_CONFIG = HookConfig()


def get_config():
    """Get current configuration (from environment variables or use default)"""
    try:
        return HookConfig.from_env()
    except (ValueError, TypeError):
        # If environment variable parsing fails, use default configuration
        return DEFAULT_CONFIG
