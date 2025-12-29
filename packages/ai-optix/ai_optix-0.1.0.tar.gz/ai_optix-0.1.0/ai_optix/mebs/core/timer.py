# SPDX-FileCopyrightText: 2025 ai-foundation-software
# SPDX-License-Identifier: Apache-2.0

import time
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
from typing import List
from contextlib import contextmanager

class BenchmarkTimer:
    """
    High-precision timer that handles CPU and GPU synchronization correctly.
    """
    def __init__(self, device: str):
        self.device = device
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.elapsed_ms: float = 0.0
        
        # GPU specific events
        self.cuda_start = None
        self.cuda_end = None
        
        if HAS_TORCH and self.device == "cuda":
            self.cuda_start = torch.cuda.Event(enable_timing=True)
            self.cuda_end = torch.cuda.Event(enable_timing=True)

    def start(self):
        if HAS_TORCH and self.device == "cuda":
            torch.cuda.synchronize() # Barrier before starting to ensure clean slate
            self.cuda_start.record()
        elif HAS_TORCH and self.device == "mps":
            torch.mps.synchronize() # Barrier
            self.start_time = time.perf_counter()
        else:
            self.start_time = time.perf_counter()

    def stop(self):
        if HAS_TORCH and self.device == "cuda":
            self.cuda_end.record()
            torch.cuda.synchronize() # Wait for event to finish
            self.elapsed_ms = self.cuda_start.elapsed_time(self.cuda_end)
        elif HAS_TORCH and self.device == "mps":
            torch.mps.synchronize()
            self.end_time = time.perf_counter()
            self.elapsed_ms = (self.end_time - self.start_time) * 1000.0
        else:
            self.end_time = time.perf_counter()
            self.elapsed_ms = (self.end_time - self.start_time) * 1000.0
    
    @contextmanager
    def measure(self):
        self.start()
        try:
            yield
        finally:
            self.stop()
            
    def get_time_ms(self) -> float:
        return self.elapsed_ms

class TimerCollection:
    """Stores multiple timing samples."""
    def __init__(self):
        self.samples_ms: List[float] = []

    def add(self, ms: float):
        self.samples_ms.append(ms)

    def reset(self):
        self.samples_ms = []
