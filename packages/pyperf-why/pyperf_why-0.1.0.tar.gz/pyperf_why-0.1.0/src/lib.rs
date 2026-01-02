use pyo3::prelude::*;

mod analyzer;
mod heuristics;
mod models;
mod report;

use models::{AnalysisInput, Report};

#[pyfunction]
fn analyze(input: AnalysisInput) -> PyResult<Report> {
    let report = analyzer::run_analysis(input);
    Ok(report)
}

#[pymodule]
fn _pyperf_why_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(analyze, m)?)?;
    m.add_class::<models::AnalysisInput>()?;
    m.add_class::<models::AstPattern>()?;
    m.add_class::<models::BytecodePattern>()?;
    m.add_class::<models::RuntimeStats>()?;
    m.add_class::<models::Report>()?;
    m.add_class::<models::Issue>()?;
    m.add_class::<models::Severity>()?;
    Ok(())
}
