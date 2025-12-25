"""Tests for verifiers/base.py - Verifier abstract base class."""

from typing import Any

import pytest

from chuk_gym_core.schemas.config import DifficultyLevel
from chuk_gym_core.schemas.problem import Problem
from chuk_gym_core.schemas.trace import Step, StepOperation, StepRef, Trace
from chuk_gym_core.schemas.verification import (
    ErrorType,
    VerificationResult,
)
from chuk_gym_core.verifiers.base import Verifier


class ConcreteVerifier(Verifier):
    """Concrete implementation for testing."""

    @property
    def domain(self) -> str:
        return "test_verifier"

    def verify_final(
        self,
        problem: Problem,
        candidate: str,
    ) -> VerificationResult:
        if problem.gold_answer is None:
            return VerificationResult.failure(
                ErrorType.INCOMPLETE,
                "No gold answer available",
            )

        if candidate.strip() == problem.gold_answer.strip():
            return VerificationResult.success(
                expected=problem.gold_answer,
                actual=candidate,
            )

        return VerificationResult.failure(
            ErrorType.WRONG_ANSWER,
            f"Expected {problem.gold_answer}, got {candidate}",
            expected=problem.gold_answer,
            actual=candidate,
        )


class NumericVerifier(Verifier):
    """Verifier for numeric answers with tolerance."""

    @property
    def domain(self) -> str:
        return "numeric_verifier"

    def verify_final(
        self,
        problem: Problem,
        candidate: str,
    ) -> VerificationResult:
        try:
            candidate_value = float(candidate)
        except ValueError:
            return VerificationResult.failure(
                ErrorType.INVALID_FORMAT,
                "Could not parse as number",
            )

        if problem.gold_answer is None:
            return VerificationResult.failure(ErrorType.INCOMPLETE)

        gold_value = float(problem.gold_answer)
        tolerance = problem.answer_tolerance or 1e-9

        if abs(candidate_value - gold_value) < tolerance:
            return VerificationResult.success(expected=gold_value, actual=candidate_value)

        return VerificationResult.failure(
            ErrorType.WRONG_ANSWER,
            expected=gold_value,
            actual=candidate_value,
        )

    def classify_error(
        self,
        problem: Problem,
        expected: Any,
        actual: Any,
    ) -> ErrorType:
        if actual is None:
            return ErrorType.INCOMPLETE

        if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
            if abs(expected) > 0 and abs(expected - actual) / abs(expected) < 0.01:
                return ErrorType.ROUNDING_ERROR
            if expected == -actual:
                return ErrorType.SIGN_ERROR

        return ErrorType.WRONG_ANSWER


class TestVerifier:
    """Tests for Verifier abstract base class."""

    @pytest.fixture
    def verifier(self) -> ConcreteVerifier:
        return ConcreteVerifier()

    @pytest.fixture
    def numeric_verifier(self) -> NumericVerifier:
        return NumericVerifier()

    @pytest.fixture
    def problem(self) -> Problem:
        return Problem(
            id="test_1",
            seed=42,
            domain="test",
            difficulty=DifficultyLevel.MEDIUM,
            prompt="What is 2 + 2?",
            gold_answer="4",
        )

    @pytest.fixture
    def trace(self) -> Trace:
        return Trace(
            problem_id="test_1",
            steps=[
                Step(
                    index=0,
                    operation=StepOperation.LITERAL,
                    before_state="2",
                    after_state="2",
                    output_value=2,
                ),
                Step(
                    index=1,
                    operation=StepOperation.LITERAL,
                    before_state="2",
                    after_state="2",
                    output_value=2,
                ),
                Step(
                    index=2,
                    operation=StepOperation.ADD,
                    before_state="2 + 2",
                    after_state="4",
                    input_refs=[StepRef(step_index=0), StepRef(step_index=1)],
                    output_value=4,
                ),
            ],
        )

    def test_domain_property(self, verifier: ConcreteVerifier):
        """Test domain property."""
        assert verifier.domain == "test_verifier"

    def test_verify_final_correct(self, verifier: ConcreteVerifier, problem: Problem):
        """Test verify_final with correct answer."""
        result = verifier.verify_final(problem, "4")

        assert result.correct is True
        assert result.score == 1.0
        assert result.error_type == ErrorType.NONE
        assert result.expected == "4"
        assert result.actual == "4"

    def test_verify_final_incorrect(self, verifier: ConcreteVerifier, problem: Problem):
        """Test verify_final with incorrect answer."""
        result = verifier.verify_final(problem, "5")

        assert result.correct is False
        assert result.error_type == ErrorType.WRONG_ANSWER
        assert result.expected == "4"
        assert result.actual == "5"

    def test_verify_final_no_gold_answer(self, verifier: ConcreteVerifier):
        """Test verify_final with no gold answer."""
        problem = Problem(
            id="test",
            seed=42,
            domain="test",
            difficulty=DifficultyLevel.EASY,
            prompt="Test",
            gold_answer=None,
        )

        result = verifier.verify_final(problem, "anything")

        assert result.correct is False
        assert result.error_type == ErrorType.INCOMPLETE

    def test_verify_step_correct(
        self,
        verifier: ConcreteVerifier,
        problem: Problem,
        trace: Trace,
    ):
        """Test verify_step with correct value."""
        result = verifier.verify_step(problem, trace, step_index=0, candidate_value=2)

        assert result.correct is True
        assert result.expected == 2
        assert result.actual == 2

    def test_verify_step_incorrect(
        self,
        verifier: ConcreteVerifier,
        problem: Problem,
        trace: Trace,
    ):
        """Test verify_step with incorrect value."""
        result = verifier.verify_step(problem, trace, step_index=0, candidate_value=5)

        assert result.correct is False
        assert result.error_type == ErrorType.WRONG_ANSWER

    def test_verify_step_out_of_range(
        self,
        verifier: ConcreteVerifier,
        problem: Problem,
        trace: Trace,
    ):
        """Test verify_step with out of range index."""
        result = verifier.verify_step(problem, trace, step_index=10, candidate_value=0)

        assert result.correct is False
        assert result.error_type == ErrorType.INVALID_FORMAT
        assert "out of range" in result.error_message.lower()

    def test_verify_step_negative_index(
        self,
        verifier: ConcreteVerifier,
        problem: Problem,
        trace: Trace,
    ):
        """Test verify_step with negative index."""
        result = verifier.verify_step(problem, trace, step_index=-1, candidate_value=0)

        assert result.correct is False
        assert result.error_type == ErrorType.INVALID_FORMAT

    def test_verify_trace_correct(
        self,
        verifier: ConcreteVerifier,
        problem: Problem,
        trace: Trace,
    ):
        """Test verify_trace with correct trace."""
        candidate_trace = Trace(
            problem_id="test_1",
            steps=[
                Step(
                    index=0,
                    operation=StepOperation.LITERAL,
                    before_state="2",
                    after_state="2",
                    output_value=2,
                ),
                Step(
                    index=1,
                    operation=StepOperation.LITERAL,
                    before_state="2",
                    after_state="2",
                    output_value=2,
                ),
                Step(
                    index=2,
                    operation=StepOperation.ADD,
                    before_state="2+2",
                    after_state="4",
                    output_value=4,
                ),
            ],
        )

        result = verifier.verify_trace(problem, trace, candidate_trace)

        assert result.correct is True
        assert result.score == 1.0
        assert result.steps_correct == 3
        assert result.steps_total == 3

    def test_verify_trace_partial_credit(
        self,
        verifier: ConcreteVerifier,
        problem: Problem,
        trace: Trace,
    ):
        """Test verify_trace with partial credit."""
        candidate_trace = Trace(
            problem_id="test_1",
            steps=[
                Step(
                    index=0,
                    operation=StepOperation.LITERAL,
                    before_state="2",
                    after_state="2",
                    output_value=2,
                ),
                Step(
                    index=1,
                    operation=StepOperation.LITERAL,
                    before_state="2",
                    after_state="2",
                    output_value=3,  # Wrong
                ),
                Step(
                    index=2,
                    operation=StepOperation.ADD,
                    before_state="2+2",
                    after_state="5",
                    output_value=5,  # Wrong
                ),
            ],
        )

        result = verifier.verify_trace(problem, trace, candidate_trace)

        assert result.correct is False
        assert result.steps_correct == 1
        assert result.steps_total == 3
        assert result.partial_credit == pytest.approx(1 / 3)
        assert result.first_error_step == 1

    def test_verify_trace_empty(
        self,
        verifier: ConcreteVerifier,
        problem: Problem,
        trace: Trace,
    ):
        """Test verify_trace with empty candidate trace."""
        candidate_trace = Trace(problem_id="test_1", steps=[])

        result = verifier.verify_trace(problem, trace, candidate_trace)

        assert result.correct is False
        assert result.error_type == ErrorType.INCOMPLETE

    def test_verify_trace_shorter_candidate(
        self,
        verifier: ConcreteVerifier,
        problem: Problem,
        trace: Trace,
    ):
        """Test verify_trace with shorter candidate trace."""
        candidate_trace = Trace(
            problem_id="test_1",
            steps=[
                Step(
                    index=0,
                    operation=StepOperation.LITERAL,
                    before_state="2",
                    after_state="2",
                    output_value=2,
                ),
            ],
        )

        result = verifier.verify_trace(problem, trace, candidate_trace)

        # Should only check available steps
        assert result.steps_correct == 1
        assert result.steps_total == 3

    def test_grade_tool_usage_default(
        self,
        verifier: ConcreteVerifier,
        problem: Problem,
    ):
        """Test default grade_tool_usage."""
        tool_calls = [
            {"name": "calculator", "args": {"expr": "2+2"}},
            {"name": "verify", "args": {"value": 4}},
        ]

        grades = verifier.grade_tool_usage(problem, tool_calls)

        assert len(grades) == 2
        assert all(g.valid for g in grades)
        assert all(g.necessary for g in grades)
        assert all(g.efficient for g in grades)
        assert grades[0].tool_name == "calculator"
        assert grades[1].tool_name == "verify"

    def test_grade_tool_usage_empty(
        self,
        verifier: ConcreteVerifier,
        problem: Problem,
    ):
        """Test grade_tool_usage with no tool calls."""
        grades = verifier.grade_tool_usage(problem, [])

        assert grades == []

    def test_grade_tool_usage_missing_name(
        self,
        verifier: ConcreteVerifier,
        problem: Problem,
    ):
        """Test grade_tool_usage with missing name."""
        tool_calls = [{"args": {"x": 1}}]

        grades = verifier.grade_tool_usage(problem, tool_calls)

        assert len(grades) == 1
        assert grades[0].tool_name == "unknown"

    def test_classify_error_default(
        self,
        verifier: ConcreteVerifier,
        problem: Problem,
    ):
        """Test default classify_error."""
        error_type = verifier.classify_error(problem, expected=4, actual=5)
        assert error_type == ErrorType.WRONG_ANSWER

    def test_classify_error_none(
        self,
        verifier: ConcreteVerifier,
        problem: Problem,
    ):
        """Test classify_error with None actual."""
        error_type = verifier.classify_error(problem, expected=4, actual=None)
        assert error_type == ErrorType.INCOMPLETE

    def test_classify_error_custom(
        self,
        numeric_verifier: NumericVerifier,
        problem: Problem,
    ):
        """Test custom classify_error."""
        # Sign error
        error_type = numeric_verifier.classify_error(problem, expected=4, actual=-4)
        assert error_type == ErrorType.SIGN_ERROR

        # Rounding error
        error_type = numeric_verifier.classify_error(problem, expected=100, actual=100.5)
        assert error_type == ErrorType.ROUNDING_ERROR

    def test_parse_answer_default(
        self,
        verifier: ConcreteVerifier,
        problem: Problem,
    ):
        """Test default parse_answer."""
        parsed = verifier.parse_answer(problem, "  42  ")
        assert parsed == "42"

    def test_format_answer_default(
        self,
        verifier: ConcreteVerifier,
        problem: Problem,
    ):
        """Test default format_answer."""
        formatted = verifier.format_answer(problem, 42)
        assert formatted == "42"


class TestNumericVerifier:
    """Tests for NumericVerifier with tolerance."""

    @pytest.fixture
    def verifier(self) -> NumericVerifier:
        return NumericVerifier()

    @pytest.fixture
    def problem(self) -> Problem:
        return Problem(
            id="test_1",
            seed=42,
            domain="numeric",
            difficulty=DifficultyLevel.MEDIUM,
            prompt="Calculate pi",
            gold_answer="3.14159",
            answer_tolerance=0.001,
        )

    def test_verify_final_within_tolerance(self, verifier: NumericVerifier, problem: Problem):
        """Test numeric verification within tolerance."""
        result = verifier.verify_final(problem, "3.1416")

        assert result.correct is True

    def test_verify_final_outside_tolerance(self, verifier: NumericVerifier, problem: Problem):
        """Test numeric verification outside tolerance."""
        result = verifier.verify_final(problem, "3.2")

        assert result.correct is False

    def test_verify_final_invalid_format(self, verifier: NumericVerifier, problem: Problem):
        """Test numeric verification with invalid format."""
        result = verifier.verify_final(problem, "not a number")

        assert result.correct is False
        assert result.error_type == ErrorType.INVALID_FORMAT
