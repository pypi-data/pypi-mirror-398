# -*- coding: utf-8 -*-
"""
Hook (replace) implementation of common communication primitives under torch.distributed.ProcessGroup,
uniformly record start time, data size, and returned work object, put them into a monitoring queue for background thread/process consumption.

Usage example:
    from patch_process_group import patch_all_process_group_prims, unpatch_all_process_group_prims, work_queue
    patch_all_process_group_prims()
    # ... run distributed code ...
    unpatch_all_process_group_prims()

Description:
- Will replace the following methods (if they exist in the ProcessGroup base class):
  allreduce, allreduce_coalesced, broadcast, reduce, allgather, allgather_base,
  gather, scatter, reduce_scatter, barrier, send, recv
- Will put the returned work (if any) and metadata into the module-level work_queue (queue.Queue).
- Provides unpatch_all_process_group_prims() to restore original methods.
- For different communication primitives, try to estimate the data size (based on the first found tensor / tensor list).

Debug logging control:
- Set environment variable PG_HOOK_DEBUG=1 to enable detailed debug logging
"""

import os
import queue
import threading
import time
import uuid
from functools import wraps

try:
    import torch
    import torch.distributed as dist
except Exception:
    # Allow module import in non-PyTorch environment, but patch function will check for dist.ProcessGroup
    torch = None
    dist = None

from . import work_monitor

# ============ Debug logging control ============
DEBUG_ENABLED = os.environ.get("PG_HOOK_DEBUG", "0") == "1"


def debug_log(msg):
    """Print debug log, only outputs when DEBUG_ENABLED=True"""
    if DEBUG_ENABLED:
        print(f"[DEBUG Python] {msg}", flush=True)


# ===============================================

# Global monitoring queue, external code can directly fetch work from here for checking
work_queue = queue.Queue()
stop_event = threading.Event()

# Save replaced original methods for restoration
_originals = {}

# List of ProcessGroup methods to try to patch
_DEFAULT_PRIMS = [
    "allreduce",
    "allreduce_coalesced",
    "broadcast",
    "reduce",
    "allgather",
    "_allgather_base",  # Private API: used by dist.all_gather_into_tensor
    "allgather_into_tensor_coalesced",
    "gather",
    "scatter",
    "reduce_scatter",
    "_reduce_scatter_base",  # Private API: used by dist.reduce_scatter_tensor
    "reduce_scatter_tensor_coalesced",
    "barrier",
    "send",
    "recv",
    "alltoall",
    "alltoall_base",
]


def _get_rank_safe():
    """Safely get current rank, returns -1 on failure"""
    try:
        if dist is not None and dist.is_initialized():
            return dist.get_rank()
    except Exception:
        pass
    return -1  # Return -1 for unknown/uninitialized, keep type consistent as int


def _compute_data_size_from_obj(obj):
    """Try to compute approximate bytes from obj (could be tensor, list/tuple of tensors, or other)."""
    if torch is None:
        return 0
    size = 0
    if torch.is_tensor(obj):
        try:
            size = obj.numel() * obj.element_size()
        except Exception:
            size = 0
    elif isinstance(obj, (list, tuple)):
        for e in obj:
            size += _compute_data_size_from_obj(e)
    # For some inplace/buffer-like parameters that cannot be reliably estimated, return 0
    return size


def _extract_data_size_from_args_kwargs(args, kwargs):
    """Find the first tensor or tensor list in args/kwargs and estimate size."""
    # Priority to args (calling order is usually more stable)
    for a in args:
        s = _compute_data_size_from_obj(a)
        if s:
            return s
    # Then search in kwargs
    for _, v in kwargs.items():
        s = _compute_data_size_from_obj(v)
        if s:
            return s
    return 0


def _make_wrapper(method_name, original_fn):
    """
    Return a wrapper to replace ProcessGroup methods.
    The wrapper records start_time, estimates data size, calls the original method and puts the returned work (if any) into work_queue.
    """

    @wraps(original_fn)
    def wrapper(self, *args, **kwargs):
        rank = _get_rank_safe()
        debug_log(f"Rank {rank}: Intercepted ProcessGroup.{method_name} call")

        start_time = time.time()
        data_size = _extract_data_size_from_args_kwargs(args, kwargs)
        op_id = str(uuid.uuid4())[:8]
        op_name = f"{method_name}_{op_id}"

        # Call original method
        try:
            work = original_fn(self, *args, **kwargs)
        except Exception as e:
            # If original method throws exception, log and continue throwing
            print(
                f"Rank {rank}: ProcessGroup.{method_name} original call threw exception: {e}"
            )
            raise

        # Enqueue monitoring info, including work (could be None or custom object)
        try:
            work_queue.put(
                {
                    "name": method_name,
                    "work": work,
                    "start_time": start_time,
                    "op_name": op_name,
                    "data_size": data_size,
                    "rank": rank,
                    "args_preview": _args_preview(args, kwargs),
                }
            )
            if data_size:
                debug_log(f"Rank {rank}: enqueued {op_name} | {data_size / 1e6:.2f}MB")
            else:
                debug_log(f"Rank {rank}: enqueued {op_name} | size unknown")
        except Exception as e:
            # Enqueue failure should not affect main flow
            print(f"Rank {rank}: Failed to enqueue communication operation: {e}")

        return work

    return wrapper


def _args_preview(args, kwargs, max_len=200):
    """Return a brief args/kwargs preview string, avoiding printing large tensor content."""
    try:
        parts = []
        for a in args:
            if torch is not None and torch.is_tensor(a):
                parts.append(f"Tensor(shape={tuple(a.size())},dtype={str(a.dtype)})")
            else:
                parts.append(repr(a))
        for k, v in kwargs.items():
            if torch is not None and torch.is_tensor(v):
                parts.append(
                    f"{k}=Tensor(shape={tuple(v.size())},dtype={str(v.dtype)})"
                )
            else:
                parts.append(f"{k}={repr(v)}")
        s = ", ".join(parts)
        if len(s) > max_len:
            return s[:max_len] + "...(truncated)"
        return s
    except Exception:
        return "<preview-unavailable>"


def patch_all_process_group_prims(methods=None):
    """
    Replace communication primitives under ProcessGroup base class (default uses _DEFAULT_PRIMS list).
    - methods: Optional list[str] specifying function names to replace.
    """
    if dist is None or not hasattr(dist, "ProcessGroup"):
        print("ProcessGroup not found in torch.distributed, cannot hook")
        return

    pg_base = dist.ProcessGroup
    to_patch = methods if methods is not None else _DEFAULT_PRIMS
    rank = _get_rank_safe()

    for name in to_patch:
        if not hasattr(pg_base, name):
            debug_log(f"ProcessGroup base class does not have {name} method, skipping")
            continue
        original = getattr(pg_base, name)
        # Prevent duplicate patching
        key = f"{pg_base.__name__}.{name}"
        if key in _originals:
            debug_log(f"{key} already hooked, skipping duplicate replacement")
            continue
        wrapper = _make_wrapper(name, original)
        try:
            _originals[key] = original
            setattr(pg_base, name, wrapper)
            debug_log(f"Rank {rank}: ProcessGroup base class {name} hooked")
        except Exception as e:
            print(f"Rank {rank}: Failed to hook {name}: {e}")


def unpatch_all_process_group_prims():
    """
    Restore functions previously replaced by patch_all_process_group_prims back to original implementation.
    """
    if dist is None or not hasattr(dist, "ProcessGroup"):
        print("ProcessGroup not found in torch.distributed, cannot unpatch")
        return

    pg_base = dist.ProcessGroup
    rank = _get_rank_safe()
    for key, original in list(_originals.items()):
        # key is "ProcessGroup.<method>"
        try:
            _, name = key.split(".", 1)
            setattr(pg_base, name, original)
            debug_log(f"Rank {rank}: ProcessGroup base class {name} restored")
            _originals.pop(key, None)
        except Exception as e:
            print(f"Rank {rank}: Failed to restore {key}: {e}")


def work_monitor_forwarder():
    """Forward work items to the work monitor"""
    debug_log("Python work_monitor forwarder thread started")
    while not stop_event.is_set():
        try:
            work_item = work_queue.get(timeout=1)
            # Send work object to work monitor, including rank info
            rank = work_item.get("rank", -1)
            work_monitor.enqueue_work(work_item["work"], work_item["op_name"], rank)
            debug_log(f"Forwarded {work_item['op_name']} to work monitor")
            work_queue.task_done()
        except queue.Empty:
            continue
    debug_log("Python work_monitor forwarder thread stopped")
