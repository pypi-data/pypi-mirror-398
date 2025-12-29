# SPDX-FileCopyrightText: 2025 ai-foundation-software
# SPDX-License-Identifier: Apache-2.0

import numpy as np
from ai_optix.benchmarks.mebs import BenchmarkRunner, BenchmarkConfig, get_device_manager

# Try importing the core extension
try:
    from ai_optix._core import Optimizer
    # OptimizationResult is used in types if checked, but here likely unused
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
    print("Optimization: Core extension NOT found.")

def core_op_benchmark(opt, data, rows, cols):
    """
    Calls the Rust/C++ optimized matrix multiplication.
    """
    # The actual API from optimizer.rs: optimize_matrix(rows, cols, data)
    # Returns OptimizationResult object
    return opt.optimize_matrix(rows, cols, data)

def run_benchmark():
    if not CORE_AVAILABLE:
        print("SKIP: ai_optix._core not found. Skipping core integration benchmark.")
        return

    # 1. Setup
    rows, cols = 1024, 1024
    device_manager = get_device_manager()
    device = device_manager.device
    
    print(f"Preparing Core Benchmark on {device}...")
    # Using numpy with float32 as required by the Rust extension
    data = np.random.rand(rows, cols).astype(np.float32)
    
    # Initialize the Rust Optimizer
    opt = Optimizer("bench_instance")

    # 2. Config
    config = BenchmarkConfig(
        name=f"Core_Optimizer_MatMul_{rows}x{cols}",
        warmup_iters=1,
        measure_iters=2,
        device="cpu (cpp_kernel)"
    )
    
    # 3. Run
    runner = BenchmarkRunner(config)
    
    # We wrap the call to fit the runner signature (no args)
    def step():
        core_op_benchmark(opt, data, rows, cols)

    print("Running ai_optix._core.Optimizer.optimize_matrix()...")
    result = runner.run(step)
    
    # Manual check of one result to print internal kernel time if we want
    # (But the runner already captures end-to-end python side latency)
    single_res = core_op_benchmark(opt, data, rows, cols)
    print(f"\nInternal Kernel Time (reported by Rust): {single_res.execution_time_ms:.4f} ms")
    print(f"Full Python Roundtrip P50: {result.metrics['p50_ms']:.4f} ms") 

if __name__ == "__main__":
    run_benchmark()
