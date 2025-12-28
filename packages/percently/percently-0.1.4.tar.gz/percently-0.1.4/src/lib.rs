mod macros;
mod models;
mod stream;

use kolmogorov_smirnov as ks;
use models::{OrdF32, OrdF64};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyAny;
use pyo3::types::PyIterator;
use stream::PercentileStream;

percentile_factory!(percentile_f32, f32, OrdF32);
percentile_factory!(percentile_f64, f64, OrdF64);

#[pyfunction]
#[pyo3(name = "stream", signature = (iterable, percentile, *, every=1))]
fn stream_iter(
    _py: Python<'_>,
    iterable: &Bound<'_, PyAny>,
    percentile: u8,
    every: usize,
) -> PyResult<PercentileStream> {
    if percentile > 100 {
        return Err(PyValueError::new_err(
            "percently.stream: percentile must be in [0, 100]",
        ));
    }
    if every == 0 {
        return Err(PyValueError::new_err(
            "percently.stream: every must be >= 1",
        ));
    }

    let iter = PyIterator::from_object(iterable)?.unbind();
    Ok(PercentileStream::new(iter, percentile, every))
}

/// A Python module implemented in Rust.
#[pymodule]
fn percently(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(percentile_f32, m)?)?;
    m.add_function(wrap_pyfunction!(percentile_f64, m)?)?;
    m.add_class::<PercentileStream>()?;
    m.add_function(wrap_pyfunction!(stream_iter, m)?)?;
    Ok(())
}
