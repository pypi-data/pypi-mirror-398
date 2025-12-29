// SPDX-FileCopyrightText: 2025 ai-foundation-software
// SPDX-License-Identifier: Apache-2.0

use super::events::MetricEvent;
use crossbeam::queue::ArrayQueue;
use std::sync::Arc;

pub struct MetricBuffer {
    queue: Arc<ArrayQueue<MetricEvent>>,
}

#[allow(dead_code)]
impl MetricBuffer {
    pub fn new(capacity: usize) -> Self {
        MetricBuffer {
            queue: Arc::new(ArrayQueue::new(capacity)),
        }
    }

    pub fn push(&self, event: MetricEvent) -> Result<(), MetricEvent> {
        self.queue.push(event)
    }

    pub fn pop(&self) -> Option<MetricEvent> {
        self.queue.pop()
    }

    pub fn drain(&self) -> Vec<MetricEvent> {
        let mut events = Vec::new();
        while let Some(event) = self.queue.pop() {
            events.push(event);
        }
        events
    }

    pub fn len(&self) -> usize {
        self.queue.len()
    }

    pub fn is_empty(&self) -> bool {
        self.queue.is_empty()
    }
}
