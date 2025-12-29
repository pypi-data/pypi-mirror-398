# SPDX-FileCopyrightText: 2025 ai-foundation-software
# SPDX-License-Identifier: Apache-2.0

import time
from typing import List
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
import numpy as np
from contextlib import contextmanager


class BenchmarkTimer:
    """
    Precision timer for benchmarking deep learning models.
    Handles device synchronization and different backend timing mechanisms.
    """
    
    def __init__(self, device_type: str = "cpu"):
        self.device_type = device_type
        self.latencies: List[float] = []
        self._start_event = None
        self._end_event = None
        self._start_time_cpu = None

    def _sync(self):
        if not HAS_TORCH:
            return
        if self.device_type == "cuda":
            torch.cuda.synchronize()
        elif self.device_type == "mps":
            # MPS sync
            if hasattr(torch, 'mps'):
                torch.mps.synchronize()
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                 # Older torch versions might not have explicit sync exposed easily, 
                 # but usually torch.cuda.synchronize() acts as a no-op or we rely on CPU blocking
                 pass

    def start_record(self):
        self._sync()
        if HAS_TORCH and self.device_type == "cuda":
            self._start_event = torch.cuda.Event(enable_timing=True)
            self._end_event = torch.cuda.Event(enable_timing=True)
            self._start_event.record()
        else:
            self._start_time_cpu = time.perf_counter()

    def stop_record(self):
        if HAS_TORCH and self.device_type == "cuda":
            self._end_event.record()
            torch.cuda.synchronize() # Wait for event to complete
            # elapsed_time is in milliseconds
            self.latencies.append(self._start_event.elapsed_time(self._end_event) / 1000.0)
        else:
            self._sync()
            end_time = time.perf_counter()
            self.latencies.append(end_time - self._start_time_cpu)

    @contextmanager
    def measure(self):
        self.start_record()
        yield
        self.stop_record()

    def get_stats(self):
        if not self.latencies:
            return {}
        
        arr = np.array(self.latencies) * 1000.0 # Convert to ms for reporting
        return {
            "p50_ms": np.percentile(arr, 50),
            "p95_ms": np.percentile(arr, 95),
            "p99_ms": np.percentile(arr, 99),
            "mean_ms": np.mean(arr),
            "std_ms": np.std(arr),
            "min_ms": np.min(arr),
            "max_ms": np.max(arr),
            "samples": len(self.latencies)
        }

    def reset(self):
        self.latencies = []

