// SPDX-FileCopyrightText: 2025 ai-foundation-software
// SPDX-License-Identifier: Apache-2.0

use lazy_static::lazy_static;
use parking_lot::Mutex;
use pyo3::prelude::*;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

pub mod buffer;
pub mod events;
pub mod ffi;
pub mod monitors;

use buffer::MetricBuffer;

const BUFFER_CAPACITY: usize = 100_000;

struct SessionState {
    buffer: Arc<MetricBuffer>,
    is_running: Arc<AtomicBool>,
    start_time: Option<std::time::Instant>,
}

lazy_static! {
    static ref SESSION: Mutex<SessionState> = Mutex::new(SessionState {
        buffer: Arc::new(MetricBuffer::new(BUFFER_CAPACITY)),
        is_running: Arc::new(AtomicBool::new(false)),
        start_time: None,
    });
}

#[pyclass]
pub struct ProfilerSession {}

#[pymethods]
impl ProfilerSession {
    #[new]
    fn new() -> Self {
        ProfilerSession {}
    }

    fn start(&self) {
        let mut session = SESSION.lock();
        if !session.is_running.load(Ordering::SeqCst) {
            session.is_running.store(true, Ordering::SeqCst);
            let now = std::time::Instant::now();
            session.start_time = Some(now);

            let running_flag = session.is_running.clone();
            let buffer = session.buffer.clone();
            let start_time = now;

            std::thread::spawn(move || {
                let mut cpu_monitor = monitors::cpu::CpuMonitor::new();
                let mut gpu_monitor = monitors::gpu::GpuMonitor::new(0);

                while running_flag.load(Ordering::Relaxed) {
                    let cpu_events = cpu_monitor.sample(start_time);
                    for e in cpu_events {
                        let _ = buffer.push(e); // Drop if full
                    }

                    let gpu_events = gpu_monitor.sample(start_time);
                    for e in gpu_events {
                        let _ = buffer.push(e);
                    }

                    std::thread::sleep(std::time::Duration::from_millis(100));
                }
                println!("Profiler Background Thread Exing");
            });

            println!("Rust Profiler Session Started");
        }
    }

    fn stop(&self) {
        let session = SESSION.lock();
        if session.is_running.load(Ordering::SeqCst) {
            session.is_running.store(false, Ordering::SeqCst);
            println!("Rust Profiler Session Stopped");
        }
    }

    fn poll(&self, _py: Python) -> Vec<(u64, String, f64)> {
        let session = SESSION.lock();
        let events = session.buffer.drain();

        events
            .into_iter()
            .map(|e| {
                let (kind_str, val) = match e.kind {
                    events::MetricKind::CpuUsageVcore(v) => ("cpu_vcore", v as f64 / 100.0),
                    events::MetricKind::MemoryUsageMb(v) => ("mem_mb", v as f64),
                    events::MetricKind::GpuPowerW(v) => ("gpu_power_w", v as f64),
                    events::MetricKind::GpuTempC(v) => ("gpu_temp_c", v as f64),
                    events::MetricKind::GpuUtil(v) => ("gpu_util", v as f64),
                    events::MetricKind::KernelStart(id) => ("kernel_start", id as f64),
                    events::MetricKind::KernelEnd(id) => ("kernel_end", id as f64),
                };
                (e.timestamp_ns, kind_str.to_string(), val)
            })
            .collect()
    }

    fn get_trace_callback(&self) -> usize {
        ffi::ai_optix_trace_callback as usize
    }
}
