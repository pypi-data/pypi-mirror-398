# SPDX-FileCopyrightText: 2025 ai-foundation-software
# SPDX-License-Identifier: Apache-2.0

import threading
import time
import torch
from .profiler.cpu import CpuProfiler
from .profiler.gpu import GpuProfiler
from typing import List, Dict

# Global storage for monitoring
metrics_log: List[Dict] = []
monitoring_active = False

class AutoOptimizer:
    def __init__(self):
        self.cpu_profiler = CpuProfiler()
        self.gpu_profiler = GpuProfiler()
        self.monitor_thread = None
        self.interval = 0.5
        
        # Tracking DataLoader speed
        self.dataloader_wait_times = []
        
    def start(self):
        global monitoring_active
        monitoring_active = True
        self._monkeypatch_dataloader()
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("[AI-Optix] Auto-Profiler Started.")

    def stop(self):
        global monitoring_active
        monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        self.gpu_profiler.shutdown()
        print("[AI-Optix] Profiling Stopped.")
        return metrics_log

    def _monitor_loop(self):
        while monitoring_active:
            cpu_stats = self.cpu_profiler.snapshot()
            gpu_stats = self.gpu_profiler.snapshot()
            
            snapshot = {
                "timestamp": time.time(),
                **cpu_stats,
                **gpu_stats,
                "dataloader_wait": sum(self.dataloader_wait_times) / len(self.dataloader_wait_times) if self.dataloader_wait_times else 0.0
            }
            metrics_log.append(snapshot)
            self.dataloader_wait_times = [] # Reset buffer
            time.sleep(self.interval)

    def _monkeypatch_dataloader(self):
        """
        Injects timing logic into torch.utils.data.DataLoader
        """
        original_iter = torch.utils.data.DataLoader.__iter__
        optimizer_ref = self

        def patched_iter(self):
            iterator = original_iter(self)
            
            # Wrap the iterator
            class TimedIterator:
                def __init__(self, inner):
                    self.inner = inner
                    self.last_time = time.time()
                
                def __iter__(self):
                    return self
                
                def __next__(self):
                    start = time.time()
                    try:
                        data = next(self.inner)
                    except StopIteration:
                        raise
                    
                    # This duration is the time we blocked waiting for data
                    duration = time.time() - start
                    optimizer_ref.dataloader_wait_times.append(duration)
                    
                    return data
            
            return TimedIterator(iterator)

        torch.utils.data.DataLoader.__iter__ = patched_iter
