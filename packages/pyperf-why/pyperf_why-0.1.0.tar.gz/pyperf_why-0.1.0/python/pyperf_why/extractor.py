"""Extract patterns from Python functions using AST and bytecode."""

import ast
import dis
import inspect
import textwrap
import sys
from typing import Callable, List

from ._pyperf_why_core import AnalysisInput, AstPattern, BytecodePattern


class AstExtractor:
    """Extract patterns from function AST."""

    def extract(self, func: Callable) -> List[AstPattern]:
        patterns = []

        try:
            source = inspect.getsource(func)
            # Dedent to remove leading whitespace
            source = textwrap.dedent(source)
            tree = ast.parse(source)
        except (OSError, TypeError, IndentationError):
            return patterns

        # Track loop depth
        self.loop_depth = 0

        for node in ast.walk(tree):
            patterns.extend(self._check_nested_loops(node))
            patterns.extend(self._check_append_in_loop(node))
            patterns.extend(self._check_call_in_loop(node))

        return patterns

    def _check_nested_loops(self, node: ast.AST) -> List[AstPattern]:
        """Detect nested loops."""
        patterns = []

        if isinstance(node, (ast.For, ast.While)):
            # Check if there's a loop inside this loop
            for child in ast.walk(node):
                if child != node and isinstance(child, (ast.For, ast.While)):
                    # Get context (simplified)
                    context = ast.unparse(node) if hasattr(ast, 'unparse') else "nested loop"
                    patterns.append(
                        AstPattern(
                            pattern_type="nested_loop",
                            line_number=node.lineno,
                            context=context[:200]  # Limit context length
                        )
                    )
                    break

        return patterns

    def _check_append_in_loop(self, node: ast.AST) -> List[AstPattern]:
        """Detect list.append() calls inside loops."""
        patterns = []

        if isinstance(node, (ast.For, ast.While)):
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    # Check if it's a .append() method call
                    if isinstance(child.func, ast.Attribute):
                        if child.func.attr == "append":
                            context = ast.unparse(child) if hasattr(ast, 'unparse') else "list.append()"
                            patterns.append(
                                AstPattern(
                                    pattern_type="append_in_loop",
                                    line_number=child.lineno,
                                    context=context[:200]
                                )
                            )

        return patterns

    def _check_call_in_loop(self, node: ast.AST) -> List[AstPattern]:
        """Detect function calls inside loops."""
        patterns = []

        if isinstance(node, (ast.For, ast.While)):
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    # Skip method calls we've already detected (like append)
                    if isinstance(child.func, ast.Name):
                        context = ast.unparse(child) if hasattr(ast, 'unparse') else "function_call()"
                        patterns.append(
                            AstPattern(
                                pattern_type="call_in_loop",
                                line_number=child.lineno,
                                context=context[:200]
                            )
                        )

        return patterns


class BytecodeExtractor:
    """Extract patterns from function bytecode."""

    def extract(self, func: Callable) -> List[BytecodePattern]:
        patterns = []

        try:
            instructions = list(dis.get_instructions(func))
        except (TypeError, AttributeError):
            return patterns

        # Count opcodes
        opcode_counts = {}
        in_loop_opcodes = set()

        # Detect backward jumps (loops) - works for Python 3.11+
        loop_ranges = []
        for i, instr in enumerate(instructions):
            # Python 3.11+ uses JUMP_BACKWARD, older versions use different opcodes
            if "JUMP_BACKWARD" in instr.opname or "JUMP_ABSOLUTE" in instr.opname:
                # Mark the range as a loop
                if instr.argval is not None:
                    loop_ranges.append((instr.argval, instr.offset))

        # Also check for FOR_ITER which indicates a for loop
        for i, instr in enumerate(instructions):
            if instr.opname == "FOR_ITER":
                # The target of FOR_ITER is after the loop
                if instr.argval is not None:
                    loop_ranges.append((instr.offset, instr.argval))

        for i, instr in enumerate(instructions):
            opcode = instr.opname

            # Track specific opcodes - updated for Python 3.11+
            # LIST_APPEND, CALL (replaces CALL_FUNCTION in 3.11+)
            if opcode in ["LIST_APPEND", "CALL_FUNCTION", "CALL", "CALL_METHOD", "PRECALL"]:
                # Normalize CALL variations
                normalized_opcode = "CALL" if "CALL" in opcode else opcode
                opcode_counts[normalized_opcode] = opcode_counts.get(normalized_opcode, 0) + 1

                # Check if instruction is within any loop range
                in_loop = any(start <= instr.offset < end for start, end in loop_ranges)
                if in_loop:
                    in_loop_opcodes.add(normalized_opcode)

        # Create patterns for tracked opcodes
        for opcode, count in opcode_counts.items():
            patterns.append(
                BytecodePattern(
                    opcode=opcode,
                    frequency=count,
                    in_loop=opcode in in_loop_opcodes
                )
            )

        return patterns


def extract_patterns(func: Callable) -> AnalysisInput:
    """Extract all patterns from a function."""
    ast_extractor = AstExtractor()
    bytecode_extractor = BytecodeExtractor()

    ast_patterns = ast_extractor.extract(func)
    bytecode_patterns = bytecode_extractor.extract(func)

    return AnalysisInput(
        function_name=func.__name__,
        ast_patterns=ast_patterns,
        bytecode_patterns=bytecode_patterns,
        runtime_stats=None  # Will be filled by runtime sampler
    )
