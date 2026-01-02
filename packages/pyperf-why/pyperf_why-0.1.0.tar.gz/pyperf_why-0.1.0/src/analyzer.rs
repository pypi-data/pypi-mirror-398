use crate::heuristics;
use crate::models::{AnalysisInput, Issue, Report};
use crate::report;

pub fn run_analysis(input: AnalysisInput) -> Report {
    let mut issues: Vec<Issue> = Vec::new();

    // Run all heuristics
    issues.extend(heuristics::detect_list_growth(&input));
    issues.extend(heuristics::detect_nested_loops(&input));
    issues.extend(heuristics::detect_calls_in_loop(&input));

    // Sort by severity
    issues.sort_by(|a, b| {
        let severity_order = |s: &crate::models::Severity| match s {
            crate::models::Severity::High => 0,
            crate::models::Severity::Medium => 1,
            crate::models::Severity::Low => 2,
        };
        severity_order(&a.severity).cmp(&severity_order(&b.severity))
    });

    let summary = report::generate_summary(&issues, &input.function_name);

    Report { issues, summary }
}