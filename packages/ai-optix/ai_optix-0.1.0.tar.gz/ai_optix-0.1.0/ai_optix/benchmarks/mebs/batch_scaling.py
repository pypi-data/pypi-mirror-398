# SPDX-FileCopyrightText: 2025 ai-foundation-software
# SPDX-License-Identifier: Apache-2.0

import time
from typing import List, Callable, Any
from ...profiler.gpu import GpuProfiler # This relies on ai_optix.profiler existing
# Ideally use absolute imports


class BatchScalingRunner:
    """
    Runs a benchmark across a range of batch sizes to generate scaling metrics.
    """
    def __init__(self, batch_sizes: List[int], func: Callable[[int], Any]):
        self.batch_sizes = batch_sizes
        self.func = func # Function taking batch_size as arg
        self.results = {}
        
    def run(self, simulate: bool = False):
        print("Running Batch Scaling Benchmark...")
        for bs in self.batch_sizes:
            print(f"  Testing batch size: {bs}")
            
            # Use profiler directly here for simplicity or reuse an existing runner
            profiler = GpuProfiler(simulate=simulate)
            profiler.start()
            
            start_t = time.time()
            # Run for a fixed number of iterations or time?
            # For scaling, we usually want stable throughput.
            # Let's say we run 50 iters per batch size
            for _ in range(20):
                self.func(bs)
            end_t = time.time()
            
            metrics = profiler.stop()
            duration = end_t - start_t
            throughput = (20 * bs) / duration
            
            self.results[bs] = {
                "throughput": throughput,
                "avg_power": metrics.energy.avg_power_w,
                "avg_util": metrics.compute.avg_utilization_pct,
                "peak_mem": metrics.memory.peak_allocated_mb
            }
            
    def get_optimal_batch_size(self, target_util: float = 80.0) -> int:
        best_bs = self.batch_sizes[0]
        min_diff = 100.0
        
        for bs, stats in self.results.items():
            diff = abs(stats['avg_util'] - target_util)
            if diff < min_diff:
                min_diff = diff
                best_bs = bs
        return best_bs

    def print_report(self):
        print("\n--- Batch Scaling Report ---")
        print(f"{'Batch':<8} {'Throughput':<12} {'Util %':<8} {'Power W':<8} {'Mem MB':<8}")
        for bs in self.batch_sizes:
            r = self.results.get(bs, {})
            print(f"{bs:<8} {r.get('throughput',0):<12.1f} {r.get('avg_util',0):<8.1f} {r.get('avg_power',0):<8.1f} {r.get('peak_mem',0):<8.1f}")
