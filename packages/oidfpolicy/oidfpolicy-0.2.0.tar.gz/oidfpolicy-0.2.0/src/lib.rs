use env_logger;
use pyo3::exceptions::*;
use pyo3::prelude::*;
use serde_json::{self, json};
use serde_json::{Map, Value};

/// Mergers the tapolicy on the top of iapolicy and returns
/// the merged policy.
#[pyfunction]
fn merge_policies(tapolicy: &str, iapolicy: &str) -> PyResult<String> {
    // TODO: Need to handle all errors properly.
    let ta_policies: Value =
        serde_json::from_str(tapolicy).map_err(|e| PyValueError::new_err(e.to_string()))?;
    let ia_policies: Value =
        serde_json::from_str(iapolicy).map_err(|e| PyValueError::new_err(e.to_string()))?;

    match oidfed_metadata_policy::merge_policies(&ta_policies, &ia_policies) {
        Ok(policy) => Ok(json!(policy).to_string()),
        Err(e) => Err(PyRuntimeError::new_err(e.to_string())),
    }
}

// Apply the given policy on the metadata and return the final metadata.
#[pyfunction]
fn apply_policy(policy: &str, metadata: &str) -> PyResult<String> {
    // TODO: Need to handle all errors properly.
    let policy_val: Map<String, Value> =
        serde_json::from_str(policy).map_err(|e| PyValueError::new_err(e.to_string()))?;

    let metadata_val: Map<String, Value> =
        serde_json::from_str(metadata).map_err(|e| PyValueError::new_err(e.to_string()))?;

    match oidfed_metadata_policy::apply_policy_document_on_metadata(&policy_val, &metadata_val) {
        Ok(policy) => Ok(json!(policy).to_string()),
        Err(e) => Err(PyRuntimeError::new_err(e.to_string())),
    }
}

/// A Python module implemented in Rust.
#[pymodule]
fn oidfpolicy(m: &Bound<'_, PyModule>) -> PyResult<()> {
    env_logger::init();
    m.add_function(wrap_pyfunction!(merge_policies, m)?)?;
    m.add_function(wrap_pyfunction!(apply_policy, m)?)?;
    Ok(())
}
