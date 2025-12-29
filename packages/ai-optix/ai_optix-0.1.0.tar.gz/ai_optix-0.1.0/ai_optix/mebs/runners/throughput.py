# SPDX-FileCopyrightText: 2025 ai-foundation-software
# SPDX-License-Identifier: Apache-2.0

from typing import Callable, Any
from .base import BenchmarkRunner
from ..core.timer import BenchmarkTimer
from ..core.stats import BenchmarkStats

from ...api import BenchmarkConfig

class ThroughputConfig(BenchmarkConfig):
    pass

class ThroughputRunner(BenchmarkRunner):
    """
    Measures maximum throughput by running a tight loop.
    Minimizes timer overhead by timing the entire batch.
    """
    
    def run(self, func: Callable[[], Any], *args, **kwargs) -> BenchmarkStats:
        self._print_header()
        
        timer = BenchmarkTimer(self.device_info.device_type)
        
        # 1. Warmup
        for _ in range(self.config.warmup_iters):
             func(*args, **kwargs)
             
        # 2. Measurement (Timer around the whole loop)
        self.start_profiling()
        timer.start()
        for _ in range(self.config.measure_iters):
            func(*args, **kwargs)
        timer.stop()
        
        total_time_ms = timer.get_time_ms()
        avg_latency_ms = total_time_ms / self.config.measure_iters
        throughput = (self.config.measure_iters / total_time_ms) * 1000.0
        
        # We can't verify P99 etc because we only have one sample (the whole batch)
        # But we produce a Stats object with the mean.
        
        sys_metrics = self.stop_profiling()
        
        if sys_metrics.energy.total_energy_j > 0:
            sys_metrics.energy.samples_per_joule = self.config.measure_iters / sys_metrics.energy.total_energy_j

        if self.config.flop_count:
             # actual_flops_per_sec = (ops/sample * samples) / duration_seconds
             # duration = total_time_ms / 1000
             duration_s = total_time_ms / 1000.0
             actual_flops = (self.config.flop_count * self.config.measure_iters) / duration_s
             sys_metrics.compute.actual_flops = actual_flops
             # efficiency? We need peak FLOPs. DeviceInfo could provide it.
             # self.device_info.peak_flops? Not implemented yet. 
             # For now, let's just populate actual_flops.
             # If we had theoretical peak:
             # sys_metrics.compute.efficiency_pct = (actual_flops / peak_flops) * 100.0

        stats = BenchmarkStats(
            p50_ms=avg_latency_ms,
            p90_ms=avg_latency_ms,
            p95_ms=avg_latency_ms,
            p99_ms=avg_latency_ms,
            mean_ms=avg_latency_ms,
            std_dev_ms=0.0,
            min_ms=avg_latency_ms, # approximate
            max_ms=avg_latency_ms, # approximate
            throughput_per_sec=throughput,
            samples=self.config.measure_iters,
            system_metrics=sys_metrics
        )
        
        self.results = stats
        print(stats)
        return stats
