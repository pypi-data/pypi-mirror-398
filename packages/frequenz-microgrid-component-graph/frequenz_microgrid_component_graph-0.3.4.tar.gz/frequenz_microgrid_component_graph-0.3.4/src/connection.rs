// License: MIT
// Copyright © 2025 Frequenz Energy-as-a-Service GmbH

use frequenz_microgrid_component_graph as cg;

use pyo3::{prelude::*, types::PyAny};

use crate::utils::extract_int;

/// A wrapper for the Python object representing a connection.
pub(crate) struct Connection {
    pub(crate) start: u64,
    pub(crate) end: u64,
    pub(crate) object: Py<PyAny>,
}

impl Connection {
    pub(crate) fn try_new(py: Python<'_>, object: Bound<'_, PyAny>) -> PyResult<Self> {
        let start = extract_int(py, object.getattr("source")?)?;
        let end = extract_int(py, object.getattr("destination")?)?;

        Ok(Connection {
            start,
            end,
            object: object.into(),
        })
    }
}

impl cg::Edge for Connection {
    fn source(&self) -> u64 {
        self.start
    }

    fn destination(&self) -> u64 {
        self.end
    }
}
