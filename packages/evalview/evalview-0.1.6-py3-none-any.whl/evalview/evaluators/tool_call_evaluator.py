"""Tool call accuracy evaluator."""

import re
from typing import List, Set, Tuple
from evalview.core.types import TestCase, ExecutionTrace, ToolEvaluation


def _normalize_tool_name(name: str) -> str:
    """Normalize tool name for comparison (lowercase, remove underscores/dashes)."""
    return re.sub(r"[-_]", "", name.lower())


def _is_case_mismatch(expected: str, actual: str) -> bool:
    """Check if two tool names differ only by case or underscore/camelCase convention."""
    return _normalize_tool_name(expected) == _normalize_tool_name(actual)


def _find_similar_tools(
    missing: List[str], unexpected: List[str]
) -> List[Tuple[str, str]]:
    """Find pairs of missing/unexpected tools that are likely the same (case mismatch)."""
    similar_pairs = []
    for m in missing:
        for u in unexpected:
            if _is_case_mismatch(m, u):
                similar_pairs.append((m, u))
    return similar_pairs


class ToolCallEvaluator:
    """Evaluates whether the agent called the expected tools."""

    def evaluate(self, test_case: TestCase, trace: ExecutionTrace) -> ToolEvaluation:
        """
        Evaluate tool call accuracy.

        Args:
            test_case: Test case with expected tools
            trace: Execution trace with actual tool calls

        Returns:
            ToolEvaluation with accuracy metrics and helpful hints
        """
        expected_tools = set(test_case.expected.tools or [])
        actual_tools = [step.tool_name for step in trace.steps]

        correct: List[str] = []
        missing: List[str] = []
        unexpected: List[str] = []

        # Check for expected tools
        for tool in expected_tools:
            if tool in actual_tools:
                correct.append(tool)
            else:
                missing.append(tool)

        # Check for unexpected tools
        for tool in actual_tools:
            if tool not in expected_tools:
                unexpected.append(tool)

        # Calculate accuracy
        accuracy = 1.0 if len(expected_tools) == 0 else len(correct) / len(expected_tools)

        # Generate helpful hints for mismatches
        hints = self._generate_hints(missing, unexpected, expected_tools, set(actual_tools))

        return ToolEvaluation(
            accuracy=accuracy,
            correct=correct,
            missing=missing,
            unexpected=unexpected,
            hints=hints,
        )

    def _generate_hints(
        self,
        missing: List[str],
        unexpected: List[str],
        expected: Set[str],
        actual: Set[str],
    ) -> List[str]:
        """Generate helpful hints for debugging tool mismatches."""
        hints: List[str] = []

        if not missing and not unexpected:
            return hints

        # Find case/naming convention mismatches
        similar_pairs = _find_similar_tools(missing, unexpected)
        for expected_name, actual_name in similar_pairs:
            hints.append(
                f"Possible naming mismatch: expected '{expected_name}' but agent called '{actual_name}'. "
                f"Update your test case to use '{actual_name}' if this is correct."
            )

        # General hints
        if similar_pairs:
            hints.append(
                "Tip: Tool names are case-sensitive. Check for snake_case vs camelCase differences."
            )
        elif missing and unexpected:
            # Tools are different, not just case mismatch
            hints.append(
                "The agent called different tools than expected. "
                "Verify your agent is configured correctly and the test case matches your agent's tool names."
            )
        elif missing and not unexpected:
            # Expected tools not called at all
            hints.append(
                "The agent did not call the expected tools. "
                "Check that your agent has access to these tools and the query triggers their use."
            )
        elif unexpected and not missing:
            # Agent called extra tools
            hints.append(
                "The agent called additional tools beyond what was expected. "
                "This may be intentional - consider adding them to expected_tools in your test case."
            )

        return hints
