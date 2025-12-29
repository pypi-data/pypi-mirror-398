# SPDX-FileCopyrightText: 2025 ai-foundation-software
# SPDX-License-Identifier: Apache-2.0

import json
import logging
from dataclasses import dataclass, asdict
from typing import Dict, Any, List

@dataclass
class BenchmarkResult:
    benchmark_name: str
    device_info: Dict[str, Any]
    metrics: Dict[str, float]
    metadata: Dict[str, Any]

class BenchmarkReporter:
    """
    Handles formatted reporting of benchmark results.
    Support JSON output and console printing.
    """
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.logger = logging.getLogger("MEBS.Reporter")

    def add_result(self, result: BenchmarkResult):
        self.results.append(result)

    def print_summary(self):
        print("\n" + "="*60)
        print(f"{'MEBS BENCHMARK SUMMARY':^60}")
        print("="*60)
        
        for res in self.results:
            print(f"\nBenchmark: {res.benchmark_name}")
            print("-" * 40)
            print("Device Info:")
            for k, v in res.device_info.items():
                print(f"  {k}: {v}")
            
            print("\nMetrics:")
            for k, v in res.metrics.items():
                # Format numbers nicely
                if "ms" in k:
                    print(f"  {k:<15}: {v:.4f}")
                else:
                    print(f"  {k:<15}: {v}")
            
            if res.metadata:
                print("\nMetadata:")
                for k, v in res.metadata.items():
                    print(f"  {k}: {v}")
            print("-" * 40)
        print("="*60 + "\n")

    def save_json(self, path: str):
        data = [asdict(r) for r in self.results]
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        self.logger.info(f"Benchmark results saved to {path}")
