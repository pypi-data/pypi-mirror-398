// SPDX-FileCopyrightText: 2025 ai-foundation-software
// SPDX-License-Identifier: Apache-2.0

use numpy::PyArrayMethods;
use pyo3::prelude::*;
use rayon::prelude::*;
use std::path::PathBuf;

#[pyclass]
pub struct DataLoader {
    batch_size: usize,
    #[allow(dead_code)]
    data_path: PathBuf,
}

#[pymethods]
impl DataLoader {
    #[new]
    fn new(data_path: String, batch_size: usize) -> Self {
        DataLoader {
            batch_size,
            data_path: PathBuf::from(data_path),
        }
    }

    fn load_batch<'py>(&self, py: Python<'py>) -> PyResult<pyo3::Bound<'py, numpy::PyArray2<f32>>> {
        let batch_size = self.batch_size;
        // Allocate flat vector
        let data: Vec<f32> = (0..batch_size * 1024)
            .into_par_iter()
            .map(|_| 1.0)
            .collect();

        let array = numpy::PyArray1::from_vec(py, data).reshape((batch_size, 1024))?;
        Ok(array)
    }

    fn parallel_process(&self) -> PyResult<String> {
        let num_threads = rayon::current_num_threads();
        Ok(format!("Processed with {} threads", num_threads))
    }
}
