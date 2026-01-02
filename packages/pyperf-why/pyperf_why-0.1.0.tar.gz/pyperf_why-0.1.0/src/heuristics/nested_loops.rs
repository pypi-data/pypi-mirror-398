use crate::models::{AnalysisInput, Issue, Severity};

pub fn detect_nested_loops(input: &AnalysisInput) -> Vec<Issue> {
    let mut issues = Vec::new();

    // Find nested loop patterns
    let nested_patterns: Vec<_> = input
        .ast_patterns
        .iter()
        .filter(|p| p.pattern_type == "nested_loop")
        .collect();

    for pattern in nested_patterns {
        // Estimate complexity based on runtime stats
        let severity = if let Some(stats) = &input.runtime_stats {
            if let Some(iterations) = stats.total_iterations {
                if iterations > 100_000 {
                    Severity::High
                } else if iterations > 10_000 {
                    Severity::Medium
                } else {
                    Severity::Low
                }
            } else {
                Severity::Medium
            }
        } else {
            Severity::Medium
        };

        let nesting_level = pattern
            .context
            .matches("for ")
            .count()
            .max(pattern.context.matches("while ").count());

        let complexity = match nesting_level {
            2 => "O(n²)",
            3 => "O(n³)",
            n if n > 3 => "O(n^k) where k is very large",
            _ => "O(n²)",
        };

        issues.push(Issue {
            severity,
            pattern: "nested_loops".to_string(),
            location: format!("line {}", pattern.line_number),
            explanation: format!(
                "Nested loops create {} complexity. Python evaluates the loop condition \
                and performs iterator protocol calls on each iteration, multiplying overhead.",
                complexity
            ),
            suggestion: "Consider: (1) using NumPy for vectorized operations, \
                (2) flattening to single loop with index math, \
                (3) using itertools.product for cartesian products, \
                (4) algorithmic improvements (e.g., hash tables instead of nested search)."
                .to_string(),
        });
    }

    issues
}