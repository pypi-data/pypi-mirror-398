mod call_in_loop;
mod list_growth;
mod nested_loops;

pub use call_in_loop::detect_calls_in_loop;
pub use list_growth::detect_list_growth;
pub use nested_loops::detect_nested_loops;