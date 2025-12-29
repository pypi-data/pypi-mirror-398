// SPDX-FileCopyrightText: 2025 ai-foundation-software
// SPDX-License-Identifier: Apache-2.0

use pyo3::prelude::*;

mod loader;
mod optimizer;
mod profiler;

use loader::DataLoader;

/// Low-level AI optimization core module
#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<profiler::ProfilerSession>()?;
    m.add_class::<optimizer::Optimizer>()?;
    m.add_class::<optimizer::OptimizationResult>()?;
    m.add_class::<DataLoader>()?;
    Ok(())
}
