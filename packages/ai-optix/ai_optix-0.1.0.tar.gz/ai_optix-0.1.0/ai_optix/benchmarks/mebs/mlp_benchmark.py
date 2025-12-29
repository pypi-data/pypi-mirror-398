# SPDX-FileCopyrightText: 2025 ai-foundation-software
# SPDX-License-Identifier: Apache-2.0

import torch
import torch.nn as nn
from ai_optix.benchmarks.mebs import BenchmarkRunner, BenchmarkConfig, get_device_manager

class SimpleMLP(nn.Module):
    def __init__(self, input_size=1024, hidden_size=4096, output_size=10):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, output_size)
        )

    def forward(self, x):
        return self.net(x)

def run_benchmark():
    # 1. Setup
    input_size = 1024
    batch_size = 64
    device_manager = get_device_manager()
    device = device_manager.device
    
    print(f"preparing MLP model on {device}...")
    model = SimpleMLP(input_size=input_size).to(device)
    model.eval()
    
    inputs = torch.randn(batch_size, input_size, device=device)
    
    # 2. Config
    config = BenchmarkConfig(
        name=f"MLP_Inference_BS{batch_size}_{device.type}",
        warmup_iters=20,
        measure_iters=100,
        device=device.type
    )
    
    # 3. Run
    # We wrap the model call in a lambda or function to match the runner signature
    def inference_step():
        with torch.no_grad():
            model(inputs)
            
    runner = BenchmarkRunner(config)
    runner.run(inference_step)

if __name__ == "__main__":
    run_benchmark()
