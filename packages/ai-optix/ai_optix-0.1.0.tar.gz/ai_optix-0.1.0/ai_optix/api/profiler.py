# SPDX-FileCopyrightText: 2025 ai-foundation-software
# SPDX-License-Identifier: Apache-2.0

import time
from .._core import ProfilerSession as RustProfiler

class Profiler:
    """ High-level wrapper for ProfilerSession. """
    def __init__(self):
        self._inner = RustProfiler()

    def snapshot(self) -> dict:
        """ Returns a snapshot of system metrics by running a brief session. """
        self._inner.start()
        time.sleep(0.15) # Wait for background thread to sample (interval is 100ms)
        self._inner.stop()
        events = self._inner.poll()
        
        # Aggregate latest values
        cpu = 0.0
        mem = 0.0
        
        # events is list of (timestamp, kind_str, val)
        for _, kind, val in events:
            if kind == "cpu_vcore":
                cpu = val  # val is already /100.0 from poll
            elif kind == "mem_mb":
                mem = val * 1024 * 1024 # Convert back to bytes for compatibility
        
        return {
            "cpu_usage_percent": cpu,
            "memory_used_bytes": mem
        }
