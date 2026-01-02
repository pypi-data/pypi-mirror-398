use crate::models::{AnalysisInput, Issue, Severity};

pub fn detect_calls_in_loop(input: &AnalysisInput) -> Vec<Issue> {
    let mut issues = Vec::new();

    // Find function calls in loops
    let call_patterns: Vec<_> = input
        .ast_patterns
        .iter()
        .filter(|p| p.pattern_type == "call_in_loop")
        .collect();

    if call_patterns.is_empty() {
        return issues;
    }

    // Check bytecode for call frequency - support both CALL_FUNCTION and CALL
    let call_count = input
        .bytecode_patterns
        .iter()
        .filter(|p| (p.opcode == "CALL_FUNCTION" || p.opcode == "CALL") && p.in_loop)
        .map(|p| p.frequency)
        .sum::<u32>();

    // Heuristic: Frequent function calls in loops
    if call_count > 10 {  // Lowered threshold from 100 to 10
        let severity = if call_count > 1000 {
            Severity::High
        } else if call_count > 500 {
            Severity::Medium
        } else {
            Severity::Low
        };

        for pattern in call_patterns {
            issues.push(Issue {
                severity: severity.clone(),
                pattern: "function_call_in_loop".to_string(),
                location: format!("line {}", pattern.line_number),
                explanation: format!(
                    "Function calls have overhead: stack frame creation, argument packing, \
                    name lookup, and return value handling. Called ~{} times in this loop. \
                    Each call costs ~100-200ns even for simple functions.",
                    call_count
                ),
                suggestion: "Consider: (1) inlining the logic if simple, \
                    (2) hoisting constant calls outside the loop, \
                    (3) using local variable for repeated attribute access, \
                    (4) caching results if function is pure."
                    .to_string(),
            });
        }
    }

    issues
}