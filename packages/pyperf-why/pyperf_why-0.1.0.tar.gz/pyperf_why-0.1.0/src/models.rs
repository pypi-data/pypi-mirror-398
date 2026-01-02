use pyo3::prelude::*;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct AnalysisInput {
    #[pyo3(get)]
    pub function_name: String,
    #[pyo3(get)]
    pub ast_patterns: Vec<AstPattern>,
    #[pyo3(get)]
    pub bytecode_patterns: Vec<BytecodePattern>,
    #[pyo3(get)]
    pub runtime_stats: Option<RuntimeStats>,
}

#[pymethods]
impl AnalysisInput {
    #[new]
    #[pyo3(signature = (function_name, ast_patterns, bytecode_patterns, runtime_stats=None))]
    fn new(
        function_name: String,
        ast_patterns: Vec<AstPattern>,
        bytecode_patterns: Vec<BytecodePattern>,
        runtime_stats: Option<RuntimeStats>,
    ) -> Self {
        Self {
            function_name,
            ast_patterns,
            bytecode_patterns,
            runtime_stats,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct AstPattern {
    #[pyo3(get)]
    pub pattern_type: String,
    #[pyo3(get)]
    pub line_number: u32,
    #[pyo3(get)]
    pub context: String,
}

#[pymethods]
impl AstPattern {
    #[new]
    fn new(pattern_type: String, line_number: u32, context: String) -> Self {
        Self {
            pattern_type,
            line_number,
            context,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct BytecodePattern {
    #[pyo3(get)]
    pub opcode: String,
    #[pyo3(get)]
    pub frequency: u32,
    #[pyo3(get)]
    pub in_loop: bool,
}

#[pymethods]
impl BytecodePattern {
    #[new]
    fn new(opcode: String, frequency: u32, in_loop: bool) -> Self {
        Self {
            opcode,
            frequency,
            in_loop,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct RuntimeStats {
    #[pyo3(get)]
    pub total_iterations: Option<u64>,
    #[pyo3(get)]
    pub execution_time_ms: f64,
}

#[pymethods]
impl RuntimeStats {
    #[new]
    #[pyo3(signature = (execution_time_ms, total_iterations=None))]
    fn new(execution_time_ms: f64, total_iterations: Option<u64>) -> Self {
        Self {
            total_iterations,
            execution_time_ms,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct Report {
    #[pyo3(get)]
    pub issues: Vec<Issue>,
    #[pyo3(get)]
    pub summary: String,
}

#[pymethods]
impl Report {
    #[new]
    fn new(issues: Vec<Issue>, summary: String) -> Self {
        Self { issues, summary }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[pyclass(eq, eq_int)]
pub enum Severity {
    High,
    Medium,
    Low,
}

#[pymethods]
impl Severity {
    fn __repr__(&self) -> String {
        format!("{:?}", self)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct Issue {
    #[pyo3(get)]
    pub severity: Severity,
    #[pyo3(get)]
    pub pattern: String,
    #[pyo3(get)]
    pub location: String,
    #[pyo3(get)]
    pub explanation: String,
    #[pyo3(get)]
    pub suggestion: String,
}

#[pymethods]
impl Issue {
    #[new]
    fn new(
        severity: Severity,
        pattern: String,
        location: String,
        explanation: String,
        suggestion: String,
    ) -> Self {
        Self {
            severity,
            pattern,
            location,
            explanation,
            suggestion,
        }
    }
}
