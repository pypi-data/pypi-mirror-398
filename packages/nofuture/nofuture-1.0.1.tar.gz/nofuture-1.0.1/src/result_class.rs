#![allow(deprecated)]
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyDict;

/// Result monad: Ok(value) | Err(message, code?, details?)
#[pyclass(name = "Result")]
pub struct PyResult {
    value: Option<PyObject>,
    error_msg: Option<String>,
    error_code: Option<String>,
    error_details: Option<PyObject>,
}

#[pymethods]
impl PyResult {
    /// Constructeur Ok
    #[staticmethod]
    pub fn ok(value: PyObject) -> Self {
        PyResult {
            value: Some(value),
            error_msg: None,
            error_code: None,
            error_details: None,
        }
    }

    /// Constructeur Err avec message, code optionnel, details optionnel
    #[staticmethod]
    #[pyo3(signature = (message, code=None, details=None))]
    pub fn err(message: String, code: Option<String>, details: Option<PyObject>) -> Self {
        PyResult {
            value: None,
            error_msg: Some(message),
            error_code: code,
            error_details: details,
        }
    }

    /// True si Ok
    pub fn is_ok(&self) -> bool {
        self.value.is_some()
    }

    /// True si Err
    pub fn is_err(&self) -> bool {
        self.error_msg.is_some()
    }

    /// Unwrap value ou ValueError si Err
    pub fn unwrap(&self, py: Python<'_>) -> PyResult2<PyObject> {
        self.value
            .as_ref()
            .ok_or_else(|| {
                let msg = self.error_msg.as_deref().unwrap_or("Unknown error");
                PyValueError::new_err(format!("Tried to unwrap an Err: {}", msg))
            })
            .map(|o| o.clone_ref(py))
    }

    /// unwrap_or(default) renvoie value ou default si Err
    pub fn unwrap_or(&self, py: Python<'_>, default: PyObject) -> PyObject {
        if let Some(o) = &self.value {
            o.clone_ref(py)
        } else {
            default
        }
    }

    /// unwrap_err() retourne (msg, code, details) ou ValueError si Ok
    pub fn unwrap_err(&self, py: Python<'_>) -> PyResult2<PyObject> {
        if let Some(msg) = &self.error_msg {
            let code = self.error_code.as_ref().map(|s| s.as_str());
            let details = self.error_details.as_ref().map(|o| o.clone_ref(py));

            let tuple = (
                msg.clone(),
                code.map(|s| s.to_string()),
                details,
            );
            Ok(tuple.into_pyobject(py)?.into_any().unbind())
        } else {
            Err(PyValueError::new_err("Tried to unwrap_err on an Ok"))
        }
    }

    /// map(fn) : applique fn à Ok, laisse Err intact
    pub fn map(&self, py: Python<'_>, func: PyObject) -> PyResult2<Self> {
        if let Some(obj) = &self.value {
            let result = func.call1(py, (obj.clone_ref(py),))?;
            Ok(PyResult::ok(result))
        } else {
            Ok(self.clone())
        }
    }

    /// map_err(fn) : applique fn à Err, laisse Ok intact
    /// fn reçoit (msg, code, details) et doit retourner (msg, code, details)
    pub fn map_err(&self, py: Python<'_>, func: PyObject) -> PyResult2<Self> {
        if self.error_msg.is_some() {
            let code = self.error_code.as_ref().map(|s| s.as_str());
            let details = self.error_details.as_ref().map(|o| o.clone_ref(py));
            let msg = self.error_msg.as_ref().unwrap().clone();

            let result = func.call1(py, (msg, code, details))?;
            let tuple: (String, Option<String>, Option<PyObject>) = result.extract(py)?;

            Ok(PyResult::err(tuple.0, tuple.1, tuple.2))
        } else {
            Ok(self.clone())
        }
    }

    /// flat_map(fn) : applique fn à Ok et attend un Result en retour
    #[pyo3(name = "flat_map")]
    pub fn flat_map(&self, py: Python<'_>, func: PyObject) -> PyResult2<Self> {
        if let Some(obj) = &self.value {
            let result = func.call1(py, (obj.clone_ref(py),))?;
            let result_py: PyResult = result.extract(py)?;
            Ok(result_py)
        } else {
            Ok(self.clone())
        }
    }

    /// and_then : alias de flat_map
    #[pyo3(name = "and_then")]
    pub fn and_then(&self, py: Python<'_>, func: PyObject) -> PyResult2<Self> {
        self.flat_map(py, func)
    }

    /// flat_map (>>): appelle func(x) sur Ok, s'attend à un Result
    pub fn __rshift__(&self, py: Python<'_>, func: PyObject) -> PyResult2<PyObject> {
        if let Some(o) = &self.value {
            let result = func.call1(py, (o.clone_ref(py),))?;
            Ok(result.into())
        } else {
            let instance = Py::new(py, self.clone())?;
            Ok(instance.into())
        }
    }

    /// unwrap_or sous forme d'opérateur |
    pub fn __or__(&self, py: Python<'_>, default: PyObject) -> PyResult2<PyObject> {
        if let Some(o) = &self.value {
            Ok(o.clone_ref(py))
        } else {
            Ok(default)
        }
    }

    /// True if Ok, False if Err (pour `if result:` en Python)
    fn __bool__(&self) -> PyResult2<bool> {
        Ok(self.value.is_some())
    }

    /// to_dict() : sérialisation en dict Python
    /// Ok  -> {"ok": true, "value": ...}
    /// Err -> {"ok": false, "error": msg, "code": ..., "details": ...}
    pub fn to_dict(&self, py: Python<'_>) -> PyResult2<PyObject> {
        let dict = PyDict::new(py);

        if let Some(value) = &self.value {
            dict.set_item("ok", true)?;
            dict.set_item("value", value.clone_ref(py))?;
        } else {
            dict.set_item("ok", false)?;
            if let Some(msg) = &self.error_msg {
                dict.set_item("error", msg.as_str())?;
            }
            if let Some(code) = &self.error_code {
                dict.set_item("code", code.as_str())?;
            }
            if let Some(details) = &self.error_details {
                dict.set_item("details", details.clone_ref(py))?;
            }
        }

        Ok(dict.into_pyobject(py)?.into_any().unbind())
    }

    /// Repr : "Ok(val)" ou "Err('msg')"
    fn __repr__(&self, py: Python<'_>) -> PyResult2<String> {
        if let Some(o) = &self.value {
            let any = o.bind(py);
            let py_str = any.str()?;
            let s = py_str.to_str()?;
            Ok(format!("Ok({})", s))
        } else if let Some(msg) = &self.error_msg {
            if let Some(code) = &self.error_code {
                Ok(format!("Err('{}', code='{}')", msg, code))
            } else {
                Ok(format!("Err('{}')", msg))
            }
        } else {
            Ok("Result(?)".to_string())
        }
    }
}

// Alias pour éviter conflit avec std::result::Result
type PyResult2<T> = std::result::Result<T, PyErr>;

/// Clone manuel
impl Clone for PyResult {
    fn clone(&self) -> Self {
        Python::with_gil(|py| PyResult {
            value: self.value.as_ref().map(|o| o.clone_ref(py)),
            error_msg: self.error_msg.clone(),
            error_code: self.error_code.clone(),
            error_details: self.error_details.as_ref().map(|o| o.clone_ref(py)),
        })
    }
}
