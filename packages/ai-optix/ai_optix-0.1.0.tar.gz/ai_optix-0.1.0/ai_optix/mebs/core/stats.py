# SPDX-FileCopyrightText: 2025 ai-foundation-software
# SPDX-License-Identifier: Apache-2.0

import math
import statistics
from dataclasses import dataclass
from typing import List, Optional
# Use string forward reference or import inside if cycle, but usually okay here if structure is clean
# To avoid circular imports if metrics imports stats (unlikely), we'll use TYPE_CHECKING or just assume it's fine.
# Actually, let's just use string forward reference in dataclass and import if needed, or import at top.
from ...profiler.metrics import SystemMetrics

@dataclass
class BenchmarkStats:
    p50_ms: float
    p90_ms: float
    p95_ms: float
    p99_ms: float
    mean_ms: float
    std_dev_ms: float
    min_ms: float
    max_ms: float
    throughput_per_sec: float
    samples: int
    system_metrics: "Optional[SystemMetrics]" = None

    def __str__(self):
        return (
            f"  P50: {self.p50_ms:.3f} ms\n"
            f"  P95: {self.p95_ms:.3f} ms\n"
            f"  P99: {self.p99_ms:.3f} ms\n"
            f"  TPS: {self.throughput_per_sec:.1f} ops/s"
        )

class MetricAggregator:
    @staticmethod
    def aggregate(latencies_ms: List[float]) -> BenchmarkStats:
        if not latencies_ms:
            raise ValueError("No samples to aggregate")
            
        latencies_ms.sort()
        n = len(latencies_ms)
        
        def percentile(p: int) -> float:
            k = (n - 1) * (p / 100.0)
            f = math.floor(k)
            c = math.ceil(k)
            if f == c:
                return latencies_ms[int(k)]
            d0 = latencies_ms[int(f)] * (c - k)
            d1 = latencies_ms[int(c)] * (k - f)
            return d0 + d1

        mean_ms = statistics.mean(latencies_ms)
        # Avoid division by zero if mean is effectively 0 (unlikely but safe)
        throughput = 1000.0 / mean_ms if mean_ms > 1e-9 else 0.0
        
        return BenchmarkStats(
            p50_ms=percentile(50),
            p90_ms=percentile(90),
            p95_ms=percentile(95),
            p99_ms=percentile(99),
            mean_ms=mean_ms,
            std_dev_ms=statistics.stdev(latencies_ms) if n > 1 else 0.0,
            min_ms=latencies_ms[0],
            max_ms=latencies_ms[-1],
            throughput_per_sec=throughput,
            samples=n
        )
