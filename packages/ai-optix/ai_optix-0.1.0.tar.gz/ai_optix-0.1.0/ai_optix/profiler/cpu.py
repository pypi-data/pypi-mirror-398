# SPDX-FileCopyrightText: 2025 ai-foundation-software
# SPDX-License-Identifier: Apache-2.0

from typing import Dict

class CpuProfiler:
    """
    Deprecated: CPU profiling is now handled by the unified Rust ProfilerSession
    accessed via GpuProfiler (renamed to SystemProfiler in future).
    """
    def snapshot(self) -> Dict[str, float]:
        return {
            "cpu_percent": 0.0,
            "ram_used_mb": 0.0,
            "ram_percent": 0.0
        }
