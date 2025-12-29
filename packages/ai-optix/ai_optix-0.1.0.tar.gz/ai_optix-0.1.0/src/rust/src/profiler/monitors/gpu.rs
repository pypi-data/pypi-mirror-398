// SPDX-FileCopyrightText: 2025 ai-foundation-software
// SPDX-License-Identifier: Apache-2.0

use crate::profiler::events::{MetricEvent, MetricKind};
use nvml_wrapper::Nvml;

pub struct GpuMonitor {
    nvml: Option<Nvml>,
    device_idx: u32,
}

impl GpuMonitor {
    pub fn new(device_idx: u32) -> Self {
        let nvml = Nvml::init().ok();
        Self { nvml, device_idx }
    }

    pub fn sample(&mut self, session_start: std::time::Instant) -> Vec<MetricEvent> {
        if self.nvml.is_none() {
            return vec![];
        }

        let nvml = self.nvml.as_ref().unwrap();
        let device = match nvml.device_by_index(self.device_idx) {
            Ok(d) => d,
            Err(_) => return vec![],
        };

        let now = std::time::Instant::now();
        let timestamp_ns = now.duration_since(session_start).as_nanos() as u64;
        let mut events = Vec::new();

        // Power
        if let Ok(power_mw) = device.power_usage() {
            events.push(MetricEvent {
                timestamp_ns,
                kind: MetricKind::GpuPowerW((power_mw / 1000) as u16),
            });
        }

        // Temp
        if let Ok(temp) =
            device.temperature(nvml_wrapper::enum_wrappers::device::TemperatureSensor::Gpu)
        {
            events.push(MetricEvent {
                timestamp_ns,
                kind: MetricKind::GpuTempC(temp as i16),
            });
        }

        // Utilization
        if let Ok(util) = device.utilization_rates() {
            events.push(MetricEvent {
                timestamp_ns,
                kind: MetricKind::GpuUtil(util.gpu as u8),
            });
        }

        events
    }
}
