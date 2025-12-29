# SPDX-FileCopyrightText: 2025 ai-foundation-software
# SPDX-License-Identifier: Apache-2.0

from typing import Tuple, Dict, Any
import math
from ..benchmarks.mebs.device_manager import DeviceManager

class SmartSelector:
    """
    Intelligent Backend Selection Logic.
    
    References concepts from TensorFlow's CostModel and NumPy's dispatching:
    - Uses a simple heuristic cost model: Cost = Compute_Cost + Transfer_Cost
    - Defaults to CPU for small data/ops to avoid launch/transfer overhead.
    - Selects GPU only when 'score' (estimated speedup) > threshold.
    """
    
    # Heuristic constants (estimated/tunable)
    CPU_GFLOPS = 100.0  # Assumed modern CPU
    GPU_GFLOPS = 10000.0 # Assumed modern GPU (100x CPU)
    PCI_BW_GBPS = 16.0  # PCIe Gen3/4 ~16GB/s
    GPU_LAUNCH_OVERHEAD_S = 0.00005 # ~50us

    def __init__(self, use_gpu_if_available: bool = True):
        self.device_manager = DeviceManager()
        self.device_info = self.device_manager.info
        self.has_gpu = self.device_info["device_type"] in ["cuda", "mps"] and use_gpu_if_available

    def select_device(self, input_shape: Tuple[int, ...], op_complexity_str: str = "linear") -> str:
        """
        Decides between 'cpu' and 'gpu' based on input size and op complexity.
        
        Args:
            input_shape: Shape of the input tensor/array.
            op_complexity_str: 'linear', 'quadratic', 'cubic' (O(N), O(N^2), O(N^3)).
        """
        if not self.has_gpu:
            return "cpu"

        num_elements = math.prod(input_shape)
        dtype_size = 4 # Assume float32
        data_size_bytes = num_elements * dtype_size
        
        # 1. Estimate Transfer Cost (Host -> Device -> Host if needed, simplified to H2D)
        # Assuming we need to move data to GPU. If data is already on GPU, cost is 0.
        # This selector checks "Where should I execute given I have data on CPU?"
        transfer_time = data_size_bytes / (self.PCI_BW_GBPS * 1024**3)
        
        # 2. Estimate Compute Cost (Ops / GFLOPS)
        if op_complexity_str == "linear":
            ops = num_elements # e.g. element-wise add
        elif op_complexity_str == "quadratic":
            ops = num_elements * math.sqrt(num_elements) # e.g. matrix-vector? approx
        elif op_complexity_str == "cubic": # Matrix mult: N^3 roughly
            N = math.pow(num_elements, 1/2) # Area -> Side
            ops = N**3
        else:
            ops = num_elements
            
        cpu_time = ops / (self.CPU_GFLOPS * 1e9)
        gpu_compute = ops / (self.GPU_GFLOPS * 1e9)
        gpu_time = gpu_compute + transfer_time + self.GPU_LAUNCH_OVERHEAD_S
        
        # 3. Decision
        # If GPU time is significantly less than CPU time, choose GPU.
        # We add a slight bias towards CPU for simplicity/stability unless GPU is 2x faster.
        if gpu_time * 1.5 < cpu_time:
            return self.device_info["device_type"] # 'cuda' or 'mps'
        else:
            return "cpu"

    def save_decision(self, decision_config: Dict[str, Any]):
        """
        'Save it' - Persist choice to a config or log.
        """
        # Placeholder for persisting configuration
        import json
        with open("backend_decision.json", "w") as f:
            json.dump(decision_config, f, indent=2)
