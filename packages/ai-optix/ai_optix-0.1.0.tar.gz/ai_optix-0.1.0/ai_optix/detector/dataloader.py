# SPDX-FileCopyrightText: 2025 ai-foundation-software
# SPDX-License-Identifier: Apache-2.0

from typing import List, Dict, Any
from .base import BaseDetector, Issue

class DataLoaderDetector(BaseDetector):
    def detect(self, metrics: List[Dict[str, Any]]) -> List[Issue]:
        issues = []
        if not metrics:
            return issues
            
        # Calculate Average Wait Time
        # "dataloader_wait" is time spent in __next__ waiting for data
        total_wait = sum(m.get("dataloader_wait", 0.0) for m in metrics)
        count = len(metrics)
        avg_wait = total_wait / count
        # Heuristic: If we wait > 0.1s on average per patch poll (0.5s interval), it's significant
        # or better, check total throughput. For MVP, check relative to interval.
        
        # If we spend > 20% of time waiting for data
        if avg_wait > 0.1: 
             issues.append(Issue(
                name="Slow DataLoader",
                severity="high" if avg_wait > 0.3 else "medium",
                evidence=f"Average data wait time: {avg_wait*1000:.2f}ms per sample poll",
                suggestion="Increase `num_workers` (e.g. 4-8) and enable `pin_memory=True`."
            ))
            
        return issues
