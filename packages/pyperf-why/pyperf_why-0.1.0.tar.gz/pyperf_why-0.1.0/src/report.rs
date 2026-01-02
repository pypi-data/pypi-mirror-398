use crate::models::Issue;

pub fn generate_summary(issues: &[Issue], function_name: &str) -> String {
    if issues.is_empty() {
        return format!("✓ No performance anti-patterns detected in '{}'", function_name);
    }

    let high_count = issues
        .iter()
        .filter(|i| matches!(i.severity, crate::models::Severity::High))
        .count();
    let medium_count = issues
        .iter()
        .filter(|i| matches!(i.severity, crate::models::Severity::Medium))
        .count();
    let low_count = issues
        .iter()
        .filter(|i| matches!(i.severity, crate::models::Severity::Low))
        .count();

    let mut summary = format!(
        "Found {} performance issue{} in '{}':\n",
        issues.len(),
        if issues.len() == 1 { "" } else { "s" },
        function_name
    );

    if high_count > 0 {
        summary.push_str(&format!("  • {} high severity\n", high_count));
    }
    if medium_count > 0 {
        summary.push_str(&format!("  • {} medium severity\n", medium_count));
    }
    if low_count > 0 {
        summary.push_str(&format!("  • {} low severity\n", low_count));
    }

    summary
}