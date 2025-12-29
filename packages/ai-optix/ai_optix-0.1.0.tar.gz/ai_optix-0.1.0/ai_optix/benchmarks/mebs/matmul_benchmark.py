# SPDX-FileCopyrightText: 2025 ai-foundation-software
# SPDX-License-Identifier: Apache-2.0

import torch
from ai_optix.benchmarks.mebs import BenchmarkRunner, BenchmarkConfig, get_device_manager

def matmul_op(a: torch.Tensor, b: torch.Tensor):
    """
    Performs matrix multiplication.
    """
    return torch.matmul(a, b)

def run_benchmark():
    # 1. Setup
    rows, cols = 4096, 4096
    device_manager = get_device_manager()
    device = device_manager.device
    
    print(f"preparing data on {device}...")
    a = torch.randn(rows, cols, device=device)
    b = torch.randn(rows, cols, device=device)
    
    # 2. Config
    config = BenchmarkConfig(
        name=f"MatMul_{rows}x{cols}_{device.type}",
        warmup_iters=10,
        measure_iters=50,
        device=device.type
    )
    
    # 3. Run
    runner = BenchmarkRunner(config)
    runner.run(matmul_op, a, b)

if __name__ == "__main__":
    run_benchmark()
