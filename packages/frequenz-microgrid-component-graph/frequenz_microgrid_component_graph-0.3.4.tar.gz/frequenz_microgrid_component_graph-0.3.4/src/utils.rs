// License: MIT
// Copyright © 2025 Frequenz Energy-as-a-Service GmbH

use pyo3::{Bound, FromPyObject, PyAny, Python, intern, types::PyAnyMethods};

pub(crate) fn extract_int<T: for<'a> FromPyObject<'a, 'a, Error = pyo3::PyErr>>(
    py: Python<'_>,
    object: Bound<'_, PyAny>,
) -> pyo3::PyResult<T> {
    object.call_method0(intern!(py, "__int__"))?.extract::<T>()
}
