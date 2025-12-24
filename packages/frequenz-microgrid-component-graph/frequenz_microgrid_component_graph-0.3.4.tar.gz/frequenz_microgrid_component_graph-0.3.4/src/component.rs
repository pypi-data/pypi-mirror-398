// License: MIT
// Copyright © 2025 Frequenz Energy-as-a-Service GmbH

use frequenz_microgrid_component_graph as cg;

use pyo3::{prelude::*, types::PyAny};

use crate::{category::category_from_python_component, utils::extract_int};

/// A wrapper for the Python object representing a component.
pub(crate) struct Component {
    pub(crate) component_id: u64,
    pub(crate) category: cg::ComponentCategory,
    pub(crate) object: Py<PyAny>,
}

impl cg::Node for Component {
    fn component_id(&self) -> u64 {
        self.component_id
    }

    fn category(&self) -> cg::ComponentCategory {
        self.category
    }
}

impl Component {
    pub(crate) fn try_new(py: Python<'_>, object: Bound<'_, PyAny>) -> PyResult<Self> {
        let component_id = extract_int(py, object.getattr("id")?)?;
        let category = category_from_python_component(py, &object)?;

        Ok(Component {
            component_id,
            category,
            object: object.into(),
        })
    }
}
