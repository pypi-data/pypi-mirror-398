# SPDX-FileCopyrightText: 2025 ai-foundation-software
# SPDX-License-Identifier: Apache-2.0

import platform
import logging
from typing import Dict, Any

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

class DeviceManager:
    """
    Manages hardware device detection and selection for MEBS.
    Prioritizes correctness and explicit reporting of hardware capabilities.
    """
    
    def __init__(self):
        self._device_info = self._detect_device()
        self.logger = logging.getLogger("MEBS.DeviceManager")

    def _detect_device(self) -> Dict[str, Any]:
        """
        Detects the best available compute device and gathers system info.
        """
        info = {
            "system": platform.system(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "pytorch_version": torch.__version__ if HAS_TORCH else "N/A",
        }

        if HAS_TORCH and torch.cuda.is_available():
            info["device_type"] = "cuda"
            info["device_name"] = torch.cuda.get_device_name(0)
            info["device_count"] = torch.cuda.device_count()
            info["cuda_version"] = torch.version.cuda
            info["cudnn_version"] = torch.backends.cudnn.version()
        elif HAS_TORCH and hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            info["device_type"] = "mps"
            info["device_name"] = "Apple Silicon GPU (MPS)" # Generic name, specific unavailable via torch API usually
            info["device_count"] = 1
        else:
            info["device_type"] = "cpu"
            info["device_name"] = platform.machine() # e.g. x86_64
            info["device_count"] = 1 # Logical usually

        return info

    @property
    def device(self) -> Any: # Returns torch.device if available, else str or None
        if HAS_TORCH:
            return torch.device(self._device_info["device_type"])
        return self._device_info["device_type"]

    @property
    def info(self) -> Dict[str, Any]:
        return self._device_info

    def log_environment(self):
        """Logs the detected environment details."""
        self.logger.info("=== MEBS Hardware Environment ===")
        for key, value in self._device_info.items():
            self.logger.info(f"{key}: {value}")
        self.logger.info("=================================")

def get_device_manager() -> DeviceManager:
    return DeviceManager()
