// License: MIT
// Copyright © 2025 Frequenz Energy-as-a-Service GmbH

use frequenz_microgrid_component_graph as cg;
use pyo3::{exceptions, prelude::*};

struct ComponentClasses<'py> {
    grid_connection_point: Bound<'py, PyAny>,
    meter: Bound<'py, PyAny>,
    battery: Bound<'py, PyAny>,
    ev_charger: Bound<'py, PyAny>,
    chp: Bound<'py, PyAny>,
    wind_turbine: Bound<'py, PyAny>,
    battery_inverter: Bound<'py, PyAny>,
    solar_inverter: Bound<'py, PyAny>,
    hybrid_inverter: Bound<'py, PyAny>,
    unspecified_component: Bound<'py, PyAny>,
}

impl<'py> ComponentClasses<'py> {
    fn try_new(py: Python<'py>) -> PyResult<Self> {
        let candidates = vec![
            "frequenz.client.microgrid.component".to_string(),
            "frequenz.client.assets.electrical_component".to_string(),
        ];

        let mut last_err: Option<PyErr> = None;
        for path in &candidates {
            match py.import(path) {
                Ok(module) => {
                    return Ok(Self {
                        grid_connection_point: module.getattr("GridConnectionPoint")?,
                        meter: module.getattr("Meter")?,
                        battery: module.getattr("Battery")?,
                        ev_charger: module.getattr("EvCharger")?,
                        chp: module.getattr("Chp")?,
                        wind_turbine: module.getattr("WindTurbine")?,
                        battery_inverter: module.getattr("BatteryInverter")?,
                        solar_inverter: module.getattr("SolarInverter")?,
                        hybrid_inverter: module.getattr("HybridInverter")?,
                        unspecified_component: module.getattr("UnspecifiedComponent")?,
                    });
                }
                Err(e) => last_err = Some(e),
            }
        }
        Err(pyo3::exceptions::PyImportError::new_err(format!(
            "Could not import a component provider. Tried: {candidates:?}. \
            Install one: pip install frequenz-component-graph[microgrid] or [assets]. \
            Last error: {last_err:?}"
        )))
    }
}

pub(crate) fn category_from_python_component(
    py: Python<'_>,
    object: &Bound<'_, PyAny>,
) -> PyResult<cg::ComponentCategory> {
    let comp_classes = ComponentClasses::try_new(py)?;

    if object.is_instance(&comp_classes.grid_connection_point)?
        || object.is(&comp_classes.grid_connection_point)
    {
        Ok(cg::ComponentCategory::GridConnectionPoint)
    } else if object.is_instance(&comp_classes.meter)? || object.is(&comp_classes.meter) {
        Ok(cg::ComponentCategory::Meter)
    } else if object.is_instance(&comp_classes.battery)? || object.is(&comp_classes.battery) {
        Ok(cg::ComponentCategory::Battery(cg::BatteryType::Unspecified))
    } else if object.is_instance(&comp_classes.ev_charger)? || object.is(&comp_classes.ev_charger) {
        Ok(cg::ComponentCategory::EvCharger(
            cg::EvChargerType::Unspecified,
        ))
    } else if object.is_instance(&comp_classes.chp)? || object.is(&comp_classes.chp) {
        Ok(cg::ComponentCategory::Chp)
    } else if object.is_instance(&comp_classes.battery_inverter)?
        || object.is(&comp_classes.battery_inverter)
    {
        Ok(cg::ComponentCategory::Inverter(cg::InverterType::Battery))
    } else if object.is_instance(&comp_classes.solar_inverter)?
        || object.is(&comp_classes.solar_inverter)
    {
        Ok(cg::ComponentCategory::Inverter(cg::InverterType::Pv))
    } else if object.is_instance(&comp_classes.hybrid_inverter)?
        || object.is(&comp_classes.hybrid_inverter)
    {
        Ok(cg::ComponentCategory::Inverter(cg::InverterType::Hybrid))
    } else if object.is_instance(&comp_classes.wind_turbine)?
        || object.is(&comp_classes.wind_turbine)
    {
        Ok(cg::ComponentCategory::WindTurbine)
    } else if object.is_instance(&comp_classes.unspecified_component)?
        || object.is(&comp_classes.unspecified_component)
    {
        Ok(cg::ComponentCategory::Unspecified)
    } else {
        Err(exceptions::PyValueError::new_err(format!(
            "Unsupported component category: {:?}",
            object
        )))
    }
}

pub(crate) fn match_category(
    category_1: cg::ComponentCategory,
    category_2: cg::ComponentCategory,
) -> bool {
    match (category_1, category_2) {
        (cg::ComponentCategory::Inverter(type_1), cg::ComponentCategory::Inverter(type_2)) => {
            match (type_1, type_2) {
                (cg::InverterType::Unspecified, _) | (_, cg::InverterType::Unspecified) => true,
                _ => type_1 == type_2,
            }
        }
        (cg::ComponentCategory::Battery(type_1), cg::ComponentCategory::Battery(type_2)) => {
            match (type_1, type_2) {
                (cg::BatteryType::Unspecified, _) | (_, cg::BatteryType::Unspecified) => true,
                _ => type_1 == type_2,
            }
        }
        (cg::ComponentCategory::EvCharger(type_1), cg::ComponentCategory::EvCharger(type_2)) => {
            match (type_1, type_2) {
                (cg::EvChargerType::Unspecified, _) | (_, cg::EvChargerType::Unspecified) => true,
                _ => type_1 == type_2,
            }
        }
        _ => category_1 == category_2,
    }
}
