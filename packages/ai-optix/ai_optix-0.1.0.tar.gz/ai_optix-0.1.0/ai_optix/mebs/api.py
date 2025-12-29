# SPDX-FileCopyrightText: 2025 ai-foundation-software
# SPDX-License-Identifier: Apache-2.0

from .runners.base import BenchmarkConfig
from .runners.latency import LatencyRunner

__all__ = ["benchmark", "BenchmarkConfig", "LatencyRunner"]

def benchmark(name: str, warmup: int = 10, measure: int = 50):
    """
    Decorator for quick benchmarking.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            config = BenchmarkConfig(name=name, warmup_iters=warmup, measure_iters=measure)
            runner = LatencyRunner(config)
            return runner.run(func, *args, **kwargs)
        return wrapper
    return decorator
