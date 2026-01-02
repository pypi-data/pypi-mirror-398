use crate::models::{AnalysisInput, Issue, Severity};
use std::collections::HashSet;

pub fn detect_list_growth(input: &AnalysisInput) -> Vec<Issue> {
    let mut issues = Vec::new();

    // Check AST for append in loop
    let append_patterns: Vec<_> = input
        .ast_patterns
        .iter()
        .filter(|p| p.pattern_type == "append_in_loop")
        .collect();

    if append_patterns.is_empty() {
        return issues;
    }

    // For Python 3.11+, .append() is compiled as CALL, not LIST_APPEND
    // Check for either LIST_APPEND or CALL opcodes in loop
    let list_append_count = input
        .bytecode_patterns
        .iter()
        .find(|p| p.opcode == "LIST_APPEND" && p.in_loop)
        .map(|p| p.frequency)
        .unwrap_or(0);

    let call_count = input
        .bytecode_patterns
        .iter()
        .find(|p| p.opcode == "CALL" && p.in_loop)
        .map(|p| p.frequency)
        .unwrap_or(0);

    // Use whichever is non-zero (LIST_APPEND for older Python, CALL for 3.11+)
    let append_count = if list_append_count > 0 { list_append_count } else { call_count };

    // Heuristic: If we see append in loop AND it happens (lowered threshold)
    // Even 1 append in a loop with AST detection is worth flagging
    if !append_patterns.is_empty() && append_count > 0 {
        let severity = if append_count > 500 {
            Severity::High
        } else if append_count > 200 {
            Severity::Medium
        } else {
            Severity::Low
        };

        // Deduplicate by line number - only report once per unique line
        let mut seen_lines = HashSet::new();

        for pattern in append_patterns {
            if seen_lines.insert(pattern.line_number) {
                issues.push(Issue {
                    severity: severity.clone(),
                    pattern: "dynamic_list_growth".to_string(),
                    location: format!("line {}", pattern.line_number),
                    explanation: format!(
                        "Python reallocates list memory on each append() call. \
                        Each reallocation copies the entire list to a new memory location. \
                        This creates O(n²) memory operations. The bytecode shows ~{} append operations.",
                        append_count
                    ),
                    suggestion: "Use list comprehension: [expr for i in range(n)] \
                        or pre-allocate: result = [None] * n, then assign values."
                        .to_string(),
                });
            }
        }
    }

    issues
}
