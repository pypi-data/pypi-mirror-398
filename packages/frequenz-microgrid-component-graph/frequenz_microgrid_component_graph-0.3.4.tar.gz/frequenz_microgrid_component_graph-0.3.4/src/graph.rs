// License: MIT
// Copyright © 2025 Frequenz Energy-as-a-Service GmbH

use std::collections::BTreeSet;

use crate::{
    FormulaGenerationError, InvalidGraphError,
    category::{category_from_python_component, match_category},
    component::Component,
    connection::Connection,
    utils::extract_int,
};
use frequenz_microgrid_component_graph::{self as cg};
use pyo3::{
    prelude::*,
    types::{PyAny, PySet, PyType},
};

#[pyclass(subclass)]
#[derive(Clone, Default, Debug)]
pub struct ComponentGraphConfig {
    config: cg::ComponentGraphConfig,
}

#[pymethods]
impl ComponentGraphConfig {
    #[new]
    #[pyo3(signature = (
        *,
        allow_component_validation_failures = false,
        allow_unconnected_components = false,
        allow_unspecified_inverters = false,
        disable_fallback_components = false,
        include_phantom_loads_in_consumer_formula = false,
        prefer_inverters_in_battery_formula = false,
        prefer_inverters_in_pv_formula = false,
        prefer_chp_in_chp_formula = false,
        prefer_ev_chargers_in_ev_formula = false,
        prefer_wind_turbines_in_wind_formula = false,
    ))]
    fn new(
        allow_component_validation_failures: bool,
        allow_unconnected_components: bool,
        allow_unspecified_inverters: bool,
        disable_fallback_components: bool,
        include_phantom_loads_in_consumer_formula: bool,
        prefer_inverters_in_battery_formula: bool,
        prefer_inverters_in_pv_formula: bool,
        prefer_chp_in_chp_formula: bool,
        prefer_ev_chargers_in_ev_formula: bool,
        prefer_wind_turbines_in_wind_formula: bool,
    ) -> Self {
        ComponentGraphConfig {
            config: cg::ComponentGraphConfig {
                allow_component_validation_failures,
                allow_unconnected_components,
                allow_unspecified_inverters,
                disable_fallback_components,
                include_phantom_loads_in_consumer_formula,
                prefer_inverters_in_battery_formula,
                prefer_inverters_in_pv_formula,
                prefer_chp_in_chp_formula,
                prefer_ev_chargers_in_ev_formula,
                prefer_wind_turbines_in_wind_formula,
            },
        }
    }
}

#[pyclass(subclass)]
pub struct ComponentGraph {
    graph: cg::ComponentGraph<Component, Connection>,
}

#[pymethods]
impl ComponentGraph {
    #[new]
    #[pyo3(
        signature = (components, connections, config=None),
        text_signature = "(components, connections, config=ComponentGraphConfig())"
    )]
    fn new(
        py: Python<'_>,
        components: Bound<'_, PyAny>,
        connections: Bound<'_, PyAny>,
        config: Option<Bound<'_, PyAny>>,
    ) -> PyResult<Self> {
        let mut wrapped_components = Vec::new();
        let mut wrapped_connections = Vec::new();
        for component in components.try_iter()? {
            wrapped_components.push(Component::try_new(py, component?)?);
        }

        for connection in connections.try_iter()? {
            wrapped_connections.push(Connection::try_new(py, connection?)?);
        }

        Ok(ComponentGraph {
            graph: cg::ComponentGraph::try_new(
                wrapped_components,
                wrapped_connections,
                match config {
                    Some(config) => config.extract::<ComponentGraphConfig>()?.config,
                    None => Default::default(),
                },
            )
            .map_err(|e| PyErr::new::<InvalidGraphError, _>(e.to_string()))?,
        })
    }

    fn component(&self, component_id: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        Python::attach(|py| {
            Ok(self
                .graph
                .component(extract_int::<u64>(py, component_id)?)
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?
                .object
                .clone_ref(py))
        })
    }

    #[classmethod]
    fn __class_getitem__(cls: Bound<'_, PyType>, _generics: Bound<'_, PyAny>) -> Py<PyType> {
        cls.into()
    }

    #[pyo3(signature = (matching_ids=None, matching_types=None))]
    fn components(
        &self,
        matching_ids: Option<Bound<'_, PyAny>>,
        matching_types: Option<Bound<'_, PyAny>>,
    ) -> PyResult<Py<PySet>> {
        let iter = self.graph.components();

        Python::attach(|py| {
            let components: Vec<_> = if let Some(component_categories) = matching_types {
                let categories: Vec<cg::ComponentCategory> =
                    if let Ok(cat_iter) = component_categories.try_iter() {
                        cat_iter
                            .map(|c| category_from_python_component(py, &c?))
                            .collect::<PyResult<_>>()?
                    } else {
                        vec![category_from_python_component(py, &component_categories)?]
                    };

                iter.filter(|c| categories.iter().any(|x| match_category(*x, c.category)))
                    .collect()
            } else {
                iter.collect()
            };

            let components: Vec<_> = if let Some(ids) = matching_ids {
                let ids_set: BTreeSet<u64> = if let Ok(id_iter) = ids.try_iter() {
                    id_iter
                        .map(|id| extract_int::<u64>(py, id?))
                        .collect::<PyResult<_>>()?
                } else {
                    BTreeSet::from([extract_int::<u64>(py, ids)?])
                };

                components
                    .into_iter()
                    .filter(|c| ids_set.contains(&c.component_id))
                    .collect()
            } else {
                components
            };

            PySet::new(py, components.iter().map(|c| c.object.bind(py))).map(|s| s.into())
        })
    }

    fn connections(&self) -> PyResult<Py<PySet>> {
        Python::attach(|py| {
            PySet::new(py, self.graph.connections().map(|c| c.object.bind(py))).map(|s| s.into())
        })
    }

    fn predecessors(&self, component_id: Bound<'_, PyAny>) -> PyResult<Py<PySet>> {
        Python::attach(|py| {
            PySet::new(
                py,
                self.graph
                    .predecessors(extract_int::<u64>(py, component_id)?)
                    .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?
                    .map(|c| c.object.bind(py)),
            )
            .map(|s| s.into())
        })
    }

    fn successors(&self, component_id: Bound<'_, PyAny>) -> PyResult<Py<PySet>> {
        Python::attach(|py| {
            PySet::new(
                py,
                self.graph
                    .successors(extract_int::<u64>(py, component_id)?)
                    .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?
                    .map(|c| c.object.bind(py)),
            )
            .map(|s| s.into())
        })
    }

    fn is_pv_meter(&self, py: Python<'_>, component_id: Bound<'_, PyAny>) -> PyResult<bool> {
        self.graph
            .is_pv_meter(extract_int::<u64>(py, component_id)?)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))
    }

    fn is_battery_meter(&self, py: Python<'_>, component_id: Bound<'_, PyAny>) -> PyResult<bool> {
        self.graph
            .is_battery_meter(extract_int::<u64>(py, component_id)?)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))
    }

    fn is_ev_charger_meter(
        &self,
        py: Python<'_>,
        component_id: Bound<'_, PyAny>,
    ) -> PyResult<bool> {
        self.graph
            .is_ev_charger_meter(extract_int::<u64>(py, component_id)?)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))
    }

    fn is_chp_meter(&self, py: Python<'_>, component_id: Bound<'_, PyAny>) -> PyResult<bool> {
        self.graph
            .is_chp_meter(extract_int::<u64>(py, component_id)?)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))
    }

    // Formula generators
    fn consumer_formula(&self) -> PyResult<String> {
        self.graph
            .consumer_formula()
            .map(|f| f.to_string())
            .map_err(|e| PyErr::new::<FormulaGenerationError, _>(e.to_string()))
    }

    fn producer_formula(&self) -> PyResult<String> {
        self.graph
            .producer_formula()
            .map(|f| f.to_string())
            .map_err(|e| PyErr::new::<FormulaGenerationError, _>(e.to_string()))
    }

    fn grid_formula(&self) -> PyResult<String> {
        self.graph
            .grid_formula()
            .map(|f| f.to_string())
            .map_err(|e| PyErr::new::<FormulaGenerationError, _>(e.to_string()))
    }

    #[pyo3(signature = (battery_ids=None))]
    fn battery_formula(
        &self,
        py: Python<'_>,
        battery_ids: Option<Bound<'_, PyAny>>,
    ) -> PyResult<String> {
        self.graph
            .battery_formula(extract_ids(py, battery_ids)?)
            .map(|f| f.to_string())
            .map_err(|e| PyErr::new::<FormulaGenerationError, _>(e.to_string()))
    }

    #[pyo3(signature = (chp_ids=None))]
    fn chp_formula(&self, py: Python<'_>, chp_ids: Option<Bound<'_, PyAny>>) -> PyResult<String> {
        self.graph
            .chp_formula(extract_ids(py, chp_ids)?)
            .map(|f| f.to_string())
            .map_err(|e| PyErr::new::<FormulaGenerationError, _>(e.to_string()))
    }

    #[pyo3(signature = (pv_inverter_ids=None))]
    fn pv_formula(
        &self,
        py: Python<'_>,
        pv_inverter_ids: Option<Bound<'_, PyAny>>,
    ) -> PyResult<String> {
        self.graph
            .pv_formula(extract_ids(py, pv_inverter_ids)?)
            .map(|f| f.to_string())
            .map_err(|e| PyErr::new::<FormulaGenerationError, _>(e.to_string()))
    }

    #[pyo3(signature = (ev_charger_ids=None))]
    fn ev_charger_formula(
        &self,
        py: Python<'_>,
        ev_charger_ids: Option<Bound<'_, PyAny>>,
    ) -> PyResult<String> {
        self.graph
            .ev_charger_formula(extract_ids(py, ev_charger_ids)?)
            .map(|f| f.to_string())
            .map_err(|e| PyErr::new::<FormulaGenerationError, _>(e.to_string()))
    }

    #[pyo3(signature = (wind_turbine_ids=None))]
    fn wind_turbine_formula(
        &self,
        py: Python<'_>,
        wind_turbine_ids: Option<Bound<'_, PyAny>>,
    ) -> PyResult<String> {
        self.graph
            .wind_turbine_formula(extract_ids(py, wind_turbine_ids)?)
            .map(|f| f.to_string())
            .map_err(|e| PyErr::new::<FormulaGenerationError, _>(e.to_string()))
    }

    fn grid_coalesce_formula(&self) -> PyResult<String> {
        self.graph
            .grid_coalesce_formula()
            .map(|f| f.to_string())
            .map_err(|e| PyErr::new::<FormulaGenerationError, _>(e.to_string()))
    }

    #[pyo3(signature = (battery_ids=None))]
    fn battery_ac_coalesce_formula(
        &self,
        py: Python<'_>,
        battery_ids: Option<Bound<'_, PyAny>>,
    ) -> PyResult<String> {
        self.graph
            .battery_ac_coalesce_formula(extract_ids(py, battery_ids)?)
            .map(|f| f.to_string())
            .map_err(|e| PyErr::new::<FormulaGenerationError, _>(e.to_string()))
    }

    #[pyo3(signature = (pv_inverter_ids=None))]
    fn pv_ac_coalesce_formula(
        &self,
        py: Python<'_>,
        pv_inverter_ids: Option<Bound<'_, PyAny>>,
    ) -> PyResult<String> {
        self.graph
            .pv_ac_coalesce_formula(extract_ids(py, pv_inverter_ids)?)
            .map(|f| f.to_string())
            .map_err(|e| PyErr::new::<FormulaGenerationError, _>(e.to_string()))
    }
}

fn extract_ids(py: Python<'_>, ids: Option<Bound<'_, PyAny>>) -> PyResult<Option<BTreeSet<u64>>> {
    if let Some(ids) = ids {
        Ok(Some(
            ids.try_iter()?
                .map(|id| extract_int::<u64>(py, id?))
                .collect::<PyResult<_>>()?,
        ))
    } else {
        Ok(None)
    }
}
