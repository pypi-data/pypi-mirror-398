use pyo3::prelude::*;
use thumbhash;

#[pyfunction(name = "rgba_to_thumb_hash")]
fn py_rgba_to_thumb_hash(py: Python, width: usize, height: usize, rgba: &[u8]) -> Vec<u8> {
    py.allow_threads(|| thumbhash::rgba_to_thumb_hash(width, height, rgba))
}

#[pyfunction(name = "thumb_hash_to_rgba")]
fn py_thumb_hash_to_rgba(py: Python, hash: &[u8]) -> PyResult<(usize, usize, Vec<u8>)> {
    py.allow_threads(|| thumbhash::thumb_hash_to_rgba(hash))
        .map_err(|_| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>("Invalid or malformed thumbhash")
        })
}

#[pyfunction(name = "thumb_hash_to_average_rgba")]
fn py_thumb_hash_to_average_rgba(py: Python, hash: &[u8]) -> PyResult<(f32, f32, f32, f32)> {
    py.allow_threads(|| thumbhash::thumb_hash_to_average_rgba(hash))
        .map_err(|_| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>("Invalid or malformed thumbhash")
        })
}

#[pyfunction(name = "thumb_hash_to_approximate_aspect_ratio")]
fn py_thumb_hash_to_approximate_aspect_ratio(py: Python, hash: &[u8]) -> PyResult<f32> {
    py.allow_threads(|| thumbhash::thumb_hash_to_approximate_aspect_ratio(hash))
        .map_err(|_| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>("Invalid or malformed thumbhash")
        })
}

#[pymodule]
fn fast_thumbhash(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(py_rgba_to_thumb_hash, m)?)?;
    m.add_function(wrap_pyfunction!(py_thumb_hash_to_rgba, m)?)?;
    m.add_function(wrap_pyfunction!(py_thumb_hash_to_average_rgba, m)?)?;
    m.add_function(wrap_pyfunction!(py_thumb_hash_to_approximate_aspect_ratio, m)?)?;
    Ok(())
}