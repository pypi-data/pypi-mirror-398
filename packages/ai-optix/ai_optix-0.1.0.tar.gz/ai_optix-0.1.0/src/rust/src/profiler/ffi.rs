// SPDX-FileCopyrightText: 2025 ai-foundation-software
// SPDX-License-Identifier: Apache-2.0

use crate::profiler::events::{MetricEvent, MetricKind};
use crate::profiler::SESSION;
use std::sync::atomic::Ordering;

#[no_mangle]
pub extern "C" fn ai_optix_trace_callback(id: u32, event_type: u32) {
    // 0 = Start, 1 = End
    let session = SESSION.lock();
    // Quick check if configured
    if !session.is_running.load(Ordering::Relaxed) {
        return;
    }

    if let Some(start) = session.start_time {
        let now = std::time::Instant::now();
        let ts = now.duration_since(start).as_nanos() as u64;
        let kind = if event_type == 0 {
            MetricKind::KernelStart(id)
        } else {
            MetricKind::KernelEnd(id)
        };

        // Non-blocking push attempt
        let _ = session.buffer.push(MetricEvent {
            timestamp_ns: ts,
            kind,
        });
    }
}
