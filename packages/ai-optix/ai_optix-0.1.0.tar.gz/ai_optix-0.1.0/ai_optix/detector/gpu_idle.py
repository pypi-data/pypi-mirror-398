# SPDX-FileCopyrightText: 2025 ai-foundation-software
# SPDX-License-Identifier: Apache-2.0

from typing import List, Dict, Any
from .base import BaseDetector, Issue

class GpuIdleDetector(BaseDetector):
    def detect(self, metrics: List[Dict[str, Any]]) -> List[Issue]:
        issues = []
        if not metrics:
            return issues
        
        # Filter metrics where GPU util is present
        gpu_utils = [m.get("gpu_util", 0.0) for m in metrics]
        if not gpu_utils:
            return issues

        avg_util = sum(gpu_utils) / len(gpu_utils)
        
        # If GPU usage is very low (< 30%)
        if avg_util < 30.0:
            issues.append(Issue(
                name="GPU Underutilization",
                severity="high" if avg_util < 10 else "medium",
                evidence=f"Average GPU Utilization is only {avg_util:.1f}%",
                suggestion="Increase batch size or check for CPU bottlenecks (Data Loading)."
            ))
            
        return issues
