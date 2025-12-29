# SPDX-FileCopyrightText: 2025 ai-foundation-software
# SPDX-License-Identifier: Apache-2.0


import time
import torch
from ai_optix.api.optimizer import AIModelOptimizer

def benchmark():
    # Setup
    size = 1_000_000
    # Create fake data
    data = [float(i) for i in range(size)]
    rows = 1000
    cols = 1000
    
    print(f"Benchmarking specific operation on {size} elements...")
    
    # AI-Optix
    opt = AIModelOptimizer("speed_bench")
    start_time = time.time()
    for _ in range(10):
        # Current impl: returns metadata, computation happens in Rust
        _ = opt.optimize(data, rows, cols)
    ai_duration = time.time() - start_time
    
    # PyTorch
    # We include tensor creation overhead to be fair to ai-optix which takes a list
    start_time = time.time()
    for _ in range(10):
        t_data = torch.tensor(data, dtype=torch.float64) # Float64 to match Rust f64
        # Simulating the operation x * 1.1
        _ = t_data * 1.1
    torch_duration = time.time() - start_time
    
    print(f"AI-Optix Total Time (10 runs): {ai_duration:.4f}s")
    print(f"PyTorch Total Time (10 runs):  {torch_duration:.4f}s")
    
    ratio = torch_duration / ai_duration if ai_duration > 0 else 0
    print(f"Speedup Factor (Torch/AI-Optix): {ratio:.2f}x")

if __name__ == "__main__":
    benchmark()
