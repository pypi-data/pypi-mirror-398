# SPDX-FileCopyrightText: 2025 ai-foundation-software
# SPDX-License-Identifier: Apache-2.0

import logging
from dataclasses import dataclass
from typing import Callable, Any

from .device_manager import get_device_manager
from .timer import BenchmarkTimer
from .reporter import BenchmarkReporter, BenchmarkResult

@dataclass
class BenchmarkConfig:
    name: str
    warmup_iters: int = 10
    measure_iters: int = 100
    device: str = "auto" # "auto", "cpu", "cuda", "mps"

class BenchmarkRunner:
    """
    Orchestrates the execution of a single benchmark.
    """
    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.device_manager = get_device_manager()
        self.logger = logging.getLogger(f"MEBS.Runner.{config.name}")
        self.timer = BenchmarkTimer(device_type=self.device_manager.device.type)
        self.reporter = BenchmarkReporter()

    def run(self, func: Callable[[Any], None], *args, **kwargs) -> BenchmarkResult:
        """
        Runs the benchmark function.
        func: The function to benchmark. specific arguments can be passed via args/kwargs.
        """
        self.logger.info(f"Starting Benchmark: {self.config.name}")
        self.device_manager.log_environment()

        # Warmup
        self.logger.info(f"Warmup ({self.config.warmup_iters} iters)...")
        for _ in range(self.config.warmup_iters):
             func(*args, **kwargs)
        
        # Measurement
        self.logger.info(f"Measurement ({self.config.measure_iters} iters)...")
        self.timer.reset()
        for _ in range(self.config.measure_iters):
            with self.timer.measure():
                 func(*args, **kwargs)
        
        stats = self.timer.get_stats()
        
        result = BenchmarkResult(
            benchmark_name=self.config.name,
            device_info=self.device_manager.info,
            metrics=stats,
            metadata={
                "warmup_iters": self.config.warmup_iters,
                "measure_iters": self.config.measure_iters
            }
        )
        
        self.reporter.add_result(result)
        self.reporter.print_summary()
        return result
