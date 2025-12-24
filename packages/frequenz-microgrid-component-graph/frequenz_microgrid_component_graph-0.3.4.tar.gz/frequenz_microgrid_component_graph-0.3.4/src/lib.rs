// License: MIT
// Copyright © 2025 Frequenz Energy-as-a-Service GmbH

//! This module defines the Python bindings for the `component_graph` library.

mod category;
mod component;
mod connection;
mod graph;
mod utils;

use pyo3::prelude::*;

pyo3::create_exception!(
    _component_graph,
    InvalidGraphError,
    pyo3::exceptions::PyException
);
pyo3::create_exception!(
    _component_graph,
    FormulaGenerationError,
    pyo3::exceptions::PyException
);

/// A Python module implemented in Rust.
#[pymodule]
mod _component_graph {
    #[pymodule_export]
    use super::FormulaGenerationError;
    #[pymodule_export]
    use super::InvalidGraphError;

    #[pymodule_export]
    use crate::graph::ComponentGraph;
    #[pymodule_export]
    use crate::graph::ComponentGraphConfig;
}
