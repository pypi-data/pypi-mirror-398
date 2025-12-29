# SPDX-FileCopyrightText: 2025 ai-foundation-software
# SPDX-License-Identifier: Apache-2.0

from typing import List, Union
import numpy as np
from .._core import Optimizer as RustOptimizer
from .._core import OptimizationResult

class AIModelOptimizer:
    """ High-level wrapper for the AI Optix Optimizer. """

    def __init__(self, name: str):
        self._inner = RustOptimizer(name)

    def optimize(self, data: Union[List[float], np.ndarray], rows: int, cols: int) -> OptimizationResult:
        """ Run matrix optimization simulation. """
        
        # Ensure data is numpy array (float32) for Rust compatibility
        if not isinstance(data, np.ndarray):
            data = np.array(data, dtype=np.float32)
        elif data.dtype != np.float32:
            data = data.astype(np.float32)
            
        return self._inner.optimize_matrix(rows, cols, data)

    def suggest_backend(self, size_bytes: int) -> str:
        """ Ask the core for a backend suggestion based on size. """
        return self._inner.suggest_backend(size_bytes)
    
    def __repr__(self):
        return str(self._inner)
