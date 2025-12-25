#![allow(deprecated)]
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
// use pyo3::IntoPyObject;

#[pyclass(name = "MayBe")]
// #[derive(IntoPyObject, IntoPyObjectRef)]
pub struct MayBe {
    inner: Option<PyObject>,
}

#[pymethods]
impl MayBe {
    /// new(None) == Nothing, new(Some(obj)) == Just(obj)
    #[new]
    pub fn new(obj: Option<PyObject>) -> Self {
        MayBe { inner: obj }
    }

    /// Constructeur Just
    #[staticmethod]
    pub fn just(obj: PyObject) -> Self {
        MayBe { inner: Some(obj) }
    }

    /// Constructeur Nothing
    #[staticmethod]
    pub fn nothing() -> Self {
        MayBe { inner: None }
    }

    /// True si Just, False si Nothing
    pub fn is_just(&self) -> bool {
        self.inner.is_some()
    }

    /// True si Nothing, False si Just
    pub fn is_nothing(&self) -> bool {
        self.inner.is_none()
    }

    /// Unwrap ou ValueError si Nothing
    pub fn unwrap(&self, py: Python<'_>) -> PyResult<PyObject> {
        self.inner
            .as_ref()
            .ok_or_else(|| PyValueError::new_err("Tried to unwrap a Nothing"))
            .map(|o| o.clone_ref(py))
    }

    /// or_else(default) renvoie la valeur interne ou default
    pub fn or_else(&self, py: Python<'_>, default: PyObject) -> PyObject {
        if let Some(o) = &self.inner {
            o.clone_ref(py)
        } else {
            default
        }
    }

    /// map(fn) : applique fn à la valeur interne et wrappe dans un nouveau MayBe
    pub fn map(&self, py: Python<'_>, func: PyObject) -> PyResult<Self> {
        if let Some(obj) = &self.inner {
            let result = func.call1(py, (obj.clone_ref(py),))?;
            Ok(MayBe::just(result))
        } else {
            Ok(MayBe::nothing())
        }
    }

    /// flat_map(fn) : applique fn à la valeur et attend un MayBe en retour
    #[pyo3(name = "flat_map")]
    pub fn flat_map(&self, py: Python<'_>, func: PyObject) -> PyResult<Self> {
        if let Some(obj) = &self.inner {
            let result = func.call1(py, (obj.clone_ref(py),))?;
            let result_maybe: MayBe = result.extract(py)?;
            Ok(result_maybe)
        } else {
            Ok(MayBe::nothing())
        }
    }

    /// flat_map (>>): appelle func(x) et s'attend à ce que ce soit déjà un MayBe
    pub fn __rshift__(&self, py: Python<'_>, func: PyObject) -> PyResult<PyObject> {
        if let Some(o) = &self.inner {
            let result = func.call1(py, (o.clone_ref(py),))?;
            Ok(result.into())
        } else {
            let instance = Py::new(py, MayBe { inner: None })?;
            Ok(instance.into())
        }
    }

    /// or_else sous forme d’opérateur |
    pub fn __or__(&self, py: Python<'_>, default: PyObject) -> PyResult<PyObject> {
        if let Some(o) = &self.inner {
            Ok(o.clone_ref(py))
        } else {
            Ok(default)
        }
    }

    /// True if Just, False if Nothing (pour `if maybe:` en Python)
    fn __bool__(&self) -> PyResult<bool> {
        Ok(self.inner.is_some())
    }

    /// Repr : "Just(val)" ou "Nothing"
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        if let Some(o) = &self.inner {
            let any = o.bind(py);
            let py_str = any.str()?;
            let s = py_str.to_str()?;
            Ok(format!("Just({})", s))
        } else {
            Ok("Nothing".to_string())
        }
    }
}

/// Implémentation manuelle de Clone car PyObject n’est pas clonable par derive
impl Clone for MayBe {
    fn clone(&self) -> Self {
        Python::with_gil(|py| {
            let cloned_inner = self.inner.as_ref().map(|o| o.clone_ref(py));
            MayBe {
                inner: cloned_inner,
            }
        })
    }
}
