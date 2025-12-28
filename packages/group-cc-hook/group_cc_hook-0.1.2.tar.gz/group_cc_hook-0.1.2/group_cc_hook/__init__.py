"""
Group Collective Communication Hook

A monitoring solution for PyTorch distributed training that hooks into all 
ProcessGroup collective communication primitives and performs timeout detection.
"""

from .run_daemon import run_daemon, stop_daemon
from .config import HookConfig, get_config

__version__ = "0.1.1"

__all__ = [
    "run_daemon",
    "stop_daemon",
    "HookConfig",
    "get_config",
]
