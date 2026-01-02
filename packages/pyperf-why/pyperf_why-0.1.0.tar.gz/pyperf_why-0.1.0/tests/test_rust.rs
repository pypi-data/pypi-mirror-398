#[cfg(test)]
mod tests {
    use why_slow::heuristics::*;
    use why_slow::models::*;

    fn create_test_input() -> AnalysisInput {
        AnalysisInput {
            function_name: "test_func".to_string(),
            ast_patterns: vec![],
            bytecode_patterns: vec![],
            runtime_stats: None,
        }
    }

    #[test]
    fn test_list_growth_detection() {
        let mut input = create_test_input();

        input.ast_patterns.push(AstPattern {
            pattern_type: "append_in_loop".to_string(),
            line_number: 10,
            context: "result.append(i)".to_string(),
        });

        input.bytecode_patterns.push(BytecodePattern {
            opcode: "LIST_APPEND".to_string(),
            frequency: 100,
            in_loop: true,
        });

        let issues = detect_list_growth(&input);

        assert!(!issues.is_empty());
        assert_eq!(issues[0].pattern, "dynamic_list_growth");
    }

    #[test]
    fn test_no_list_growth_when_low_frequency() {
        let mut input = create_test_input();

        input.ast_patterns.push(AstPattern {
            pattern_type: "append_in_loop".to_string(),
            line_number: 10,
            context: "result.append(i)".to_string(),
        });

        input.bytecode_patterns.push(BytecodePattern {
            opcode: "LIST_APPEND".to_string(),
            frequency: 10, // Too low
            in_loop: true,
        });

        let issues = detect_list_growth(&input);

        assert!(issues.is_empty());
    }

    #[test]
    fn test_nested_loops_detection() {
        let mut input = create_test_input();

        input.ast_patterns.push(AstPattern {
            pattern_type: "nested_loop".to_string(),
            line_number: 5,
            context: "for i in range(n):\n    for j in range(m):".to_string(),
        });

        let issues = detect_nested_loops(&input);

        assert!(!issues.is_empty());
        assert_eq!(issues[0].pattern, "nested_loops");
        assert!(issues[0].explanation.contains("O(n²)"));
    }

    #[test]
    fn test_call_in_loop_detection() {
        let mut input = create_test_input();

        input.ast_patterns.push(AstPattern {
            pattern_type: "call_in_loop".to_string(),
            line_number: 15,
            context: "helper(i)".to_string(),
        });

        input.bytecode_patterns.push(BytecodePattern {
            opcode: "CALL_FUNCTION".to_string(),
            frequency: 150,
            in_loop: true,
        });

        let issues = detect_calls_in_loop(&input);

        assert!(!issues.is_empty());
        assert_eq!(issues[0].pattern, "function_call_in_loop");
    }

    #[test]
    fn test_severity_levels() {
        let mut input = create_test_input();

        input.ast_patterns.push(AstPattern {
            pattern_type: "append_in_loop".to_string(),
            line_number: 10,
            context: "result.append(i)".to_string(),
        });

        // High frequency = High severity
        input.bytecode_patterns.push(BytecodePattern {
            opcode: "LIST_APPEND".to_string(),
            frequency: 1000,
            in_loop: true,
        });

        let issues = detect_list_growth(&input);

        assert!(!issues.is_empty());
        assert_eq!(issues[0].severity, Severity::High);
    }

    #[test]
    fn test_no_issues_clean_code() {
        let input = create_test_input();

        let list_issues = detect_list_growth(&input);
        let loop_issues = detect_nested_loops(&input);
        let call_issues = detect_calls_in_loop(&input);

        assert!(list_issues.is_empty());
        assert!(loop_issues.is_empty());
        assert!(call_issues.is_empty());
    }
}