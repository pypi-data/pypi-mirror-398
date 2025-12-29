# SPDX-FileCopyrightText: 2025 ai-foundation-software
# SPDX-License-Identifier: Apache-2.0

import platform
import subprocess
from dataclasses import dataclass
from typing import Optional
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

@dataclass
class DeviceInfo:
    device_type: str  # "cuda", "mps", "cpu"
    device_name: str  # e.g. "NVIDIA A100", "Apple M1 Max"
    driver_version: str = "N/A"
    memory_total_gb: float = 0.0
    
    def __str__(self) -> str:
        return f"{self.device_name} ({self.device_type.upper()}) | Driver: {self.driver_version} | Mem: {self.memory_total_gb:.1f}GB"

class DeviceProbe:
    """
    Detects and reports the hardware environment for benchmarking.
    Ensures that we are measuring what we think we are measuring.
    """
    
    @staticmethod
    def get_device_info(target_device: Optional[str] = None) -> DeviceInfo:
        """
        Detects the best available device or verifies the target device.
        """
        # If user requests specific device, verify it exists.
        if target_device is None:
            if HAS_TORCH and torch.cuda.is_available():
                target_device = "cuda"
            elif HAS_TORCH and hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                target_device = "mps"
            else:
                target_device = "cpu"

        if target_device == "cuda":
            return DeviceProbe._probe_cuda()
        elif target_device == "mps":
            return DeviceProbe._probe_mps()
        else:
            return DeviceProbe._probe_cpu()

    @staticmethod
    def _probe_cuda() -> DeviceInfo:
        if not HAS_TORCH or not torch.cuda.is_available():
            # Fallback if forced
            return DeviceProbe._probe_cpu()
            
        props = torch.cuda.get_device_properties(0)
        
        # Try to get driver version via nvidia-smi if possible, currently using torch version as proxy if unavailable
        driver_ver = torch.version.cuda
        
        return DeviceInfo(
            device_type="cuda",
            device_name=props.name,
            driver_version=f"CUDA {driver_ver}",
            memory_total_gb=props.total_memory / (1024**3)
        )

    @staticmethod
    def _probe_mps() -> DeviceInfo:
        # MPS doesn't expose as much metadata via PyTorch yet
        return DeviceInfo(
            device_type="mps",
            device_name=f"Apple Silicon ({platform.machine()})",
            driver_version=platform.mac_ver()[0],
            memory_total_gb=DeviceProbe._get_system_memory_gb() # Unified memory
        )

    @staticmethod
    def _probe_cpu() -> DeviceInfo:
        return DeviceInfo(
            device_type="cpu",
            device_name=DeviceProbe._get_cpu_name(),
            driver_version="OS Kernel",
            memory_total_gb=DeviceProbe._get_system_memory_gb()
        )

    @staticmethod
    def _get_cpu_name() -> str:
        try:
            if platform.system() == "Linux":
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if "model name" in line:
                            return line.split(":")[1].strip()
            elif platform.system() == "Darwin":
                return subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).strip().decode()
        except Exception:
            pass
        return platform.processor()

    @staticmethod
    def _get_system_memory_gb() -> float:
        import psutil
        return psutil.virtual_memory().total / (1024**3)
