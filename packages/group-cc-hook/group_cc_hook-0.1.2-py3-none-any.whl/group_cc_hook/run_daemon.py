"""
Start timeout detection thread to check if work objects timeout
Stop timeout detection thread
"""

import atexit
import threading

try:
    import torch
    import torch.distributed as dist
except Exception:
    # Allow module import in non-PyTorch environment, but patch function will check for dist.ProcessGroup
    torch = None
    dist = None

from . import work_monitor
from .patch_all_collective_primi import (
    patch_all_process_group_prims,
    stop_event,
    work_monitor_forwarder,
    work_queue,
)

monitor_thread = None
_daemon_started = False


def run_daemon(config=None):
    global monitor_thread, _daemon_started

    if _daemon_started:
        return

    # Start Python work monitoring thread
    work_monitor.start_monitor(config=config)
    # Start Python forwarding thread
    monitor_thread = threading.Thread(target=work_monitor_forwarder, daemon=True)
    monitor_thread.start()

    patch_all_process_group_prims()

    _daemon_started = True
    # Register cleanup function to run at exit
    atexit.register(stop_daemon)


def stop_daemon():
    global _daemon_started

    if not _daemon_started:
        return

    # Stop Python forwarding thread
    work_queue.join()
    stop_event.set()
    if monitor_thread is not None:
        monitor_thread.join()
    # Stop Python monitoring thread
    work_monitor.stop_monitor()

    _daemon_started = False
