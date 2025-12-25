use pyo3::prelude::*;
mod maybe_class;
mod result_class;

// Make MayBe and Result available when importing nofut from Python
pub use maybe_class::MayBe;
pub use result_class::PyResult as Result;

#[pymodule]
fn nofut(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<MayBe>()?;
    m.add_class::<result_class::PyResult>()?;
    Ok(())
}
