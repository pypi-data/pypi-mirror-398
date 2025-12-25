"""
Abstract base class for answer/trace verifiers.

All domain-specific verifiers should inherit from Verifier
to ensure a consistent interface across the system.
"""

from abc import ABC, abstractmethod
from typing import Any

from chuk_gym_core.schemas.problem import Problem
from chuk_gym_core.schemas.trace import Trace
from chuk_gym_core.schemas.verification import (
    ErrorType,
    ToolCallGrade,
    VerificationResult,
)


class Verifier(ABC):
    """
    Abstract base class for answer verification.

    All domain verifiers (ArithmeticVerifier, SudokuVerifier, etc.)
    should inherit from this class to ensure interface consistency.

    Verifiers handle:
    - Final answer verification
    - Step-by-step trace verification
    - Partial credit calculation
    - Error classification
    - Tool usage grading

    Example:
        class MyDomainVerifier(Verifier):
            def verify_final(self, problem, candidate):
                if candidate == problem.gold_answer:
                    return VerificationResult.success()
                return VerificationResult.failure()
    """

    @property
    @abstractmethod
    def domain(self) -> str:
        """Domain identifier for this verifier."""
        pass

    @abstractmethod
    def verify_final(
        self,
        problem: Problem,
        candidate: str,
    ) -> VerificationResult:
        """
        Verify a final answer submission.

        Args:
            problem: The problem being solved
            candidate: The candidate answer string

        Returns:
            VerificationResult with correctness, score, and error info
        """
        pass

    def verify_step(
        self,
        problem: Problem,
        trace: Trace,
        step_index: int,
        candidate_value: Any,
    ) -> VerificationResult:
        """
        Verify a single step's output.

        Default implementation uses the trace's verify_step method.
        Override for domain-specific step verification.

        Args:
            problem: The problem being solved
            trace: The expected solution trace
            step_index: Index of the step to verify
            candidate_value: The candidate value for this step

        Returns:
            VerificationResult for this step
        """
        if step_index < 0 or step_index >= len(trace.steps):
            return VerificationResult.failure(
                ErrorType.INVALID_FORMAT,
                f"Step index {step_index} out of range",
            )

        expected_step = trace.steps[step_index]
        if expected_step.verify_output(candidate_value):
            return VerificationResult.success(
                expected=expected_step.output_value,
                actual=candidate_value,
            )
        else:
            return VerificationResult.failure(
                ErrorType.WRONG_ANSWER,
                f"Step {step_index} incorrect",
                expected=expected_step.output_value,
                actual=candidate_value,
            )

    def verify_trace(
        self,
        problem: Problem,
        expected_trace: Trace,
        candidate_trace: Trace,
    ) -> VerificationResult:
        """
        Verify a complete solution trace.

        Default implementation verifies each step and calculates partial credit.

        Args:
            problem: The problem being solved
            expected_trace: The expected solution trace
            candidate_trace: The candidate solution trace

        Returns:
            VerificationResult with step-level details
        """
        if not candidate_trace.steps:
            return VerificationResult.failure(
                ErrorType.INCOMPLETE,
                "Empty trace",
            )

        correct_steps = 0
        first_error = None

        for i, step in enumerate(candidate_trace.steps):
            if i >= len(expected_trace.steps):
                break

            if expected_trace.steps[i].verify_output(step.output_value):
                correct_steps += 1
            elif first_error is None:
                first_error = i

        total_steps = len(expected_trace.steps)
        partial_credit = correct_steps / total_steps if total_steps > 0 else 0.0

        # Check final answer
        final_correct = expected_trace.verify_final(candidate_trace.final_value)

        if final_correct and correct_steps == total_steps:
            return VerificationResult(
                correct=True,
                score=1.0,
                partial_credit=1.0,
                error_type=ErrorType.NONE,
                steps_correct=correct_steps,
                steps_total=total_steps,
            )
        else:
            if first_error is not None:
                error_msg = f"Trace incorrect at step {first_error}"
            else:
                error_msg = "Final answer incorrect"
            return VerificationResult(
                correct=False,
                score=partial_credit,
                partial_credit=partial_credit,
                error_type=ErrorType.WRONG_ANSWER,
                error_message=error_msg,
                steps_correct=correct_steps,
                steps_total=total_steps,
                first_error_step=first_error,
            )

    def grade_tool_usage(
        self,
        problem: Problem,
        tool_calls: list[dict[str, Any]],
    ) -> list[ToolCallGrade]:
        """
        Grade tool usage for a problem.

        Default implementation returns valid grades for all calls.
        Override for domain-specific tool grading.

        Args:
            problem: The problem being solved
            tool_calls: List of tool call dicts with 'name' and 'args'

        Returns:
            List of ToolCallGrade for each tool call
        """
        return [
            ToolCallGrade(
                tool_name=call.get("name", "unknown"),
                args=call.get("args", {}),
                valid=True,
                necessary=True,
                efficient=True,
            )
            for call in tool_calls
        ]

    def classify_error(
        self,
        problem: Problem,
        expected: Any,
        actual: Any,
    ) -> ErrorType:
        """
        Classify the type of error made.

        Default implementation returns WRONG_ANSWER.
        Override for domain-specific error classification.

        Args:
            problem: The problem being solved
            expected: Expected answer
            actual: Actual (incorrect) answer

        Returns:
            ErrorType classification
        """
        if actual is None:
            return ErrorType.INCOMPLETE
        return ErrorType.WRONG_ANSWER

    def parse_answer(
        self,
        problem: Problem,
        answer_str: str,
    ) -> Any:
        """
        Parse an answer string into the appropriate type.

        Default implementation returns the string as-is.
        Override for domain-specific parsing.

        Args:
            problem: The problem context
            answer_str: The raw answer string

        Returns:
            Parsed answer value
        """
        return answer_str.strip()

    def format_answer(
        self,
        problem: Problem,
        value: Any,
    ) -> str:
        """
        Format an answer value as a string.

        Default implementation returns str(value).
        Override for domain-specific formatting.

        Args:
            problem: The problem context
            value: The answer value

        Returns:
            Formatted answer string
        """
        return str(value)
