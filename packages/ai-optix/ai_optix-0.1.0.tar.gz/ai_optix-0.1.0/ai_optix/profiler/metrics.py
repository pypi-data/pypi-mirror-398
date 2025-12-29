# SPDX-FileCopyrightText: 2025 ai-foundation-software
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from typing import List

@dataclass
class TimeSeriesData:
    timestamps: List[float]
    values: List[float]

@dataclass
class EnergyMetrics:
    avg_power_w: float
    max_power_w: float
    total_energy_j: float
    samples_per_joule: float
    idle_power_w: float
    power_history: TimeSeriesData

@dataclass
class MemoryMetrics:
    peak_allocated_mb: float
    peak_reserved_mb: float
    fragmentation_ratio: float
    memory_history: TimeSeriesData

@dataclass
class ThermalMetrics:
    max_temp_c: float
    avg_temp_c: float
    temp_delta_c: float
    throttled: bool
    temp_history: TimeSeriesData

@dataclass
class ComputeMetrics:
    avg_utilization_pct: float
    utilization_history: TimeSeriesData
    theoretical_flops: float = 0.0
    actual_flops: float = 0.0
    efficiency_pct: float = 0.0

@dataclass
class SystemMetrics:
    energy: EnergyMetrics
    memory: MemoryMetrics
    thermal: ThermalMetrics
    compute: ComputeMetrics
