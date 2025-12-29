// SPDX-FileCopyrightText: 2025 ai-foundation-software
// SPDX-License-Identifier: Apache-2.0

use numpy::PyReadonlyArrayDyn;
use pyo3::prelude::*;
use serde::{Deserialize, Serialize};

#[pyclass]
#[derive(Debug, Serialize, Deserialize)]
pub struct OptimizationResult {
    #[pyo3(get)]
    pub execution_time_ms: f64,
    #[pyo3(get)]
    pub optimized: bool,
    #[pyo3(get)]
    pub device: String,
}

#[pyclass]
pub struct Optimizer {
    name: String,
}

extern "C" {
    fn mat_mul_cpu(a: *const f32, b: *const f32, c: *mut f32, m: i32, n: i32, k: i32);
    fn init_profiler_cb(addr: usize);
}

#[pymethods]
impl Optimizer {
    #[new]
    pub fn new(name: String) -> Self {
        unsafe {
            use crate::profiler::ffi::ai_optix_trace_callback;
            init_profiler_cb(ai_optix_trace_callback as usize);
        }
        Optimizer { name }
    }

    /// Optimizes matrix (MatMul simulation via C++)
    /// Accepts a 2D numpy array (flattened or not) and treats it as Square Matrix of side `rows`
    /// Current demo assumes input `data` is A, and we multiply A * A for demo purposes.
    pub fn optimize_matrix(
        &self,
        _py: Python,
        rows: usize,
        cols: usize,
        data: PyReadonlyArrayDyn<f32>,
    ) -> PyResult<OptimizationResult> {
        let start = std::time::Instant::now();

        let a_slice = data.as_slice()?;
        let len = a_slice.len();

        if len != rows * cols {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "Data size {} does not match rows*cols {}",
                len,
                rows * cols
            )));
        }

        // Allocate result buffer (C)
        // For A * A where A is rows*cols (assuming square for simplicity or matching dim)
        // If Rows != Cols this logic needs update. Assuming Rows=Cols for demo.
        let mut c = vec![0.0f32; rows * cols];

        unsafe {
            mat_mul_cpu(
                a_slice.as_ptr(),
                a_slice.as_ptr(), // Multiplying by self for demo
                c.as_mut_ptr(),
                rows as i32,
                cols as i32,
                cols as i32, // K = cols
            );
        }

        let duration = start.elapsed();

        Ok(OptimizationResult {
            execution_time_ms: duration.as_secs_f64() * 1000.0,
            optimized: true,
            device: "cpu (cpp_kernel)".to_string(),
        })
    }

    /// Suggests best backend based on data size
    pub fn suggest_backend(&self, size_bytes: u64) -> String {
        if size_bytes > 1024 * 1024 * 100 {
            // 100 MB
            "gpu".to_string()
        } else {
            "cpu".to_string()
        }
    }

    pub fn __repr__(&self) -> String {
        format!("<Optimizer name='{}'>", self.name)
    }
}
