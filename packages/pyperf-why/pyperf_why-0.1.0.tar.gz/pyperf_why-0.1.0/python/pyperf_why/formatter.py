"""Format analysis reports for terminal output."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._why_slow_core import Report, Issue, Severity


# ANSI color codes
class Colors:
    RED = "\033[91m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
    GRAY = "\033[90m"


def format_report(report: "Report") -> str:
    """Format a report for terminal output with colors."""
    lines = []

    # Summary
    lines.append(f"\n{Colors.BOLD}{report.summary}{Colors.RESET}\n")

    if not report.issues:
        return "".join(lines)

    # Issues
    for i, issue in enumerate(report.issues, 1):
        lines.append(format_issue(issue, i))
        lines.append("")  # Blank line between issues

    return "\n".join(lines)


def format_issue(issue: "Issue", number: int) -> str:
    """Format a single issue."""
    # Severity icon and color
    severity_str = str(issue.severity)
    if "High" in severity_str:
        icon = "🔴"
        color = Colors.RED
    elif "Medium" in severity_str:
        icon = "🟡"
        color = Colors.YELLOW
    else:
        icon = "🟢"
        color = Colors.GREEN

    lines = []

    # Header
    lines.append(
        f"{icon} {color}{Colors.BOLD}Issue #{number}: {issue.pattern}{Colors.RESET}"
    )
    lines.append(f"   {Colors.GRAY}Location: {issue.location}{Colors.RESET}")

    # Explanation
    lines.append(f"\n   {Colors.BOLD}Why it's slow:{Colors.RESET}")
    lines.append(f"   {wrap_text(issue.explanation, indent=3)}")

    # Suggestion
    lines.append(f"\n   {Colors.BOLD}How to fix:{Colors.RESET}")
    lines.append(f"   {Colors.BLUE}{wrap_text(issue.suggestion, indent=3)}{Colors.RESET}")

    return "\n".join(lines)


def wrap_text(text: str, width: int = 80, indent: int = 0) -> str:
    """Wrap text to specified width with indent."""
    words = text.split()
    lines = []
    current_line = []
    current_length = indent

    for word in words:
        word_length = len(word) + 1  # +1 for space
        if current_length + word_length > width and current_line:
            lines.append(" " * indent + " ".join(current_line))
            current_line = [word]
            current_length = indent + len(word)
        else:
            current_line.append(word)
            current_length += word_length

    if current_line:
        lines.append(" " * indent + " ".join(current_line))

    return "\n   ".join(lines) if lines else ""