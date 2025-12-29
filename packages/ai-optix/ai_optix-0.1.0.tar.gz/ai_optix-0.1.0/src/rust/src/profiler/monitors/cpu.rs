// SPDX-FileCopyrightText: 2025 ai-foundation-software
// SPDX-License-Identifier: Apache-2.0

use crate::profiler::events::{MetricEvent, MetricKind};
use sysinfo::{CpuRefreshKind, MemoryRefreshKind, RefreshKind, System};

pub struct CpuMonitor {
    sys: System,
}

impl CpuMonitor {
    pub fn new() -> Self {
        Self {
            sys: System::new_with_specifics(
                RefreshKind::new()
                    .with_cpu(CpuRefreshKind::everything())
                    .with_memory(MemoryRefreshKind::everything()),
            ),
        }
    }

    pub fn sample(&mut self, session_start: std::time::Instant) -> Vec<MetricEvent> {
        self.sys.refresh_cpu();
        self.sys.refresh_memory();

        let now = std::time::Instant::now();
        let timestamp_ns = now.duration_since(session_start).as_nanos() as u64;

        let cpu_usage = self.sys.global_cpu_info().cpu_usage();
        let memory_used = self.sys.used_memory(); // Bytes

        // Scaled for u16: 100.0% -> 10000
        let cpu_scaled = (cpu_usage * 100.0) as u16;
        let mem_mb = (memory_used / 1024 / 1024) as u32;

        vec![
            MetricEvent {
                timestamp_ns,
                kind: MetricKind::CpuUsageVcore(cpu_scaled),
            },
            MetricEvent {
                timestamp_ns,
                kind: MetricKind::MemoryUsageMb(mem_mb),
            },
        ]
    }
}
