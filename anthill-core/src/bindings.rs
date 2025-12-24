use pyo3::prelude::*;
use pyo3::types::PyDict;
use crate::engine::TickEngine;
use crate::types::state::GameState;

#[pyclass]
pub struct PyGameState {
    pub inner: GameState,
}

#[pymethods]
impl PyGameState {
    #[new]
    fn new() -> Self {
        PyGameState {
            inner: GameState::new(),
        }
    }

    #[staticmethod]
    fn from_json(json: &str) -> PyResult<Self> {
        match GameState::from_json(json) {
            Ok(state) => Ok(PyGameState { inner: state }),
            Err(e) => Err(pyo3::exceptions::PyValueError::new_err(format!("Invalid JSON: {}", e))),
        }
    }

    fn to_json(&self) -> PyResult<String> {
        match self.inner.to_json() {
            Ok(json) => Ok(json),
            Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(format!("Serialization failed: {}", e))),
        }
    }
}

#[pyclass]
pub struct PyTickEngine {
    inner: TickEngine,
}

#[pymethods]
impl PyTickEngine {
    #[new]
    fn new(seed: u64) -> Self {
        PyTickEngine {
            inner: TickEngine::new(seed),
        }
    }

    fn tick(&mut self, state: &mut PyGameState) -> PyResult<String> {
        let events = self.inner.tick(&mut state.inner);
        // Serialize events to JSON string to pass back to Python
        // This is a simple way to handle complex return types
        match serde_json::to_string(&events.into_events()) {
             Ok(json) => Ok(json),
             Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(format!("Event serialization failed: {}", e))),
        }
    }
}

/// The python module definition
#[pymodule]
fn anthill_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<PyGameState>()?;
    m.add_class::<PyTickEngine>()?;
    Ok(())
}
