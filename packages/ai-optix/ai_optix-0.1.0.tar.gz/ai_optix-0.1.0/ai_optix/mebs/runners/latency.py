# SPDX-FileCopyrightText: 2025 ai-foundation-software
# SPDX-License-Identifier: Apache-2.0

from typing import Callable, Any
from .base import BenchmarkRunner
from ..core.timer import BenchmarkTimer, TimerCollection
from ..core.stats import MetricAggregator, BenchmarkStats

class LatencyRunner(BenchmarkRunner):
    """
    Measures individual execution latency of a function.
    Best for inference tasks or single-op benchmarks.
    """
    
    def run(self, func: Callable[[], Any], *args, **kwargs) -> BenchmarkStats:
        self._print_header()
        
        timer = BenchmarkTimer(self.device_info.device_type)
        collector = TimerCollection()
        
        # 1. Warmup
        # print("  [Warmup Phase]...")
        for _ in range(self.config.warmup_iters):
            func(*args, **kwargs)
            
        # 2. Measurement
        # print("  [Measurement Phase]...")
        for _ in range(self.config.measure_iters):
            timer.start()
            func(*args, **kwargs)
            timer.stop()
            collector.add(timer.get_time_ms())
            
        # 3. Aggregation
        stats = MetricAggregator.aggregate(collector.samples_ms)
        self.results = stats
        
        print(stats)
        return stats
