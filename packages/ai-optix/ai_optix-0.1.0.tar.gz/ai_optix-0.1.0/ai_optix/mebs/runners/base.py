# SPDX-FileCopyrightText: 2025 ai-foundation-software
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional
from ..core.device import DeviceProbe, DeviceInfo
from ..core.stats import BenchmarkStats

from ...profiler.gpu import GpuProfiler

class BenchmarkConfig:
    def __init__(
        self,
        name: str,
        warmup_iters: int = 10,
        measure_iters: int = 100,
        device: Optional[str] = None,
        flop_count: Optional[float] = None
    ):
        self.name = name
        self.warmup_iters = warmup_iters
        self.measure_iters = measure_iters
        self.device = device
        self.flop_count = flop_count



class BenchmarkRunner(ABC):
    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.device_info: DeviceInfo = DeviceProbe.get_device_info(config.device)
        self.results: Optional[BenchmarkStats] = None
        self.profiler = GpuProfiler()
        
    def start_profiling(self):
        self.profiler.start()
        
    def stop_profiling(self):
        return self.profiler.stop()

    @abstractmethod
    def run(self, func: Callable[[], Any], *args, **kwargs) -> BenchmarkStats:
        """
        Execute the benchmark.
        """
        pass
        
    def _print_header(self):
        print(f"\n{'='*60}")
        print(f"BENCHMARK: {self.config.name}")
        print(f"DEVICE:    {self.device_info}")
        print(f"WARMUP:    {self.config.warmup_iters} iterations")
        print(f"MEASURE:   {self.config.measure_iters} iterations")
        print(f"{'='*60}")
