"""Tests for core schemas."""

from datetime import datetime

import pytest

from chuk_gym_core.schemas.config import (
    DifficultyLevel,
    DifficultyProfile,
    SolverConfig,
)
from chuk_gym_core.schemas.episode import (
    EpisodeRecord,
    EpisodeStatus,
)
from chuk_gym_core.schemas.problem import Problem
from chuk_gym_core.schemas.trace import Step, StepOperation, StepRef, Trace
from chuk_gym_core.schemas.verification import (
    ErrorType,
    ToolCallGrade,
    VerificationResult,
)


class TestDifficultyLevel:
    """Tests for DifficultyLevel enum."""

    def test_all_levels_exist(self):
        """Verify all 7 difficulty levels exist."""
        levels = list(DifficultyLevel)
        assert len(levels) == 7
        assert DifficultyLevel.VERY_EASY in levels
        assert DifficultyLevel.VERY_HARD in levels

    def test_from_simple(self):
        """Test conversion from 3-level to 7-level."""
        assert DifficultyLevel.from_simple("easy") == DifficultyLevel.EASY
        assert DifficultyLevel.from_simple("medium") == DifficultyLevel.MEDIUM
        assert DifficultyLevel.from_simple("hard") == DifficultyLevel.HARD

    def test_to_simple(self):
        """Test conversion from 7-level to 3-level."""
        assert DifficultyLevel.VERY_EASY.to_simple() == "easy"
        assert DifficultyLevel.EASY.to_simple() == "easy"
        assert DifficultyLevel.MEDIUM.to_simple() == "medium"
        assert DifficultyLevel.HARD.to_simple() == "hard"
        assert DifficultyLevel.VERY_HARD.to_simple() == "hard"

    def test_numeric_ordering(self):
        """Test numeric difficulty ordering."""
        assert DifficultyLevel.VERY_EASY.numeric == 1
        assert DifficultyLevel.VERY_HARD.numeric == 7
        assert DifficultyLevel.MEDIUM.numeric == 4


class TestSolverConfig:
    """Tests for SolverConfig."""

    def test_default_config(self):
        """Test default solver config."""
        config = SolverConfig()
        assert config.solver_allowed is True
        assert config.hint_budget == 100
        assert config.hint_penalty == 0.0

    def test_solver_free(self):
        """Test solver-free configuration."""
        config = SolverConfig.solver_free()
        assert config.solver_allowed is False
        assert config.hint_budget == 0

    def test_solver_assisted(self):
        """Test solver-assisted configuration."""
        config = SolverConfig.solver_assisted(budget=10, penalty=0.1)
        assert config.solver_allowed is True
        assert config.hint_budget == 10
        assert config.hint_penalty == 0.1

    def test_frozen(self):
        """Test that config is immutable."""
        config = SolverConfig()
        with pytest.raises(Exception):  # Pydantic frozen model
            config.hint_budget = 50


class TestDifficultyProfile:
    """Tests for DifficultyProfile."""

    def test_default_profile(self):
        """Test default profile values."""
        profile = DifficultyProfile()
        assert profile.logic_depth == 1
        assert profile.branching_factor == 1.0
        assert profile.state_observability == 1.0

    def test_estimated_complexity(self):
        """Test complexity calculation."""
        profile = DifficultyProfile(logic_depth=4, branching_factor=2.0)
        assert profile.estimated_complexity == 4 * 2.0 * (2 - 1.0)

    def test_from_difficulty_level(self):
        """Test creating profile from difficulty level."""
        easy = DifficultyProfile.from_difficulty_level(DifficultyLevel.EASY)
        hard = DifficultyProfile.from_difficulty_level(DifficultyLevel.HARD)

        assert easy.logic_depth < hard.logic_depth
        assert easy.branching_factor < hard.branching_factor


class TestProblem:
    """Tests for Problem schema."""

    def test_create_problem(self):
        """Test basic problem creation."""
        problem = Problem(
            id="test_1",
            seed=42,
            domain="arithmetic",
            difficulty=DifficultyLevel.MEDIUM,
            prompt="What is 2 + 2?",
            gold_answer="4",
        )
        assert problem.id == "test_1"
        assert problem.seed == 42
        assert problem.domain == "arithmetic"
        assert problem.gold_answer == "4"

    def test_generate_id(self):
        """Test ID generation."""
        problem_id = Problem.generate_id("arithmetic", DifficultyLevel.EASY, 12345)
        assert problem_id == "arithmetic_easy_12345"

    def test_to_prompt_dict(self):
        """Test prompt dict export."""
        problem = Problem(
            id="test_1",
            seed=42,
            domain="arithmetic",
            difficulty=DifficultyLevel.MEDIUM,
            prompt="What is 2 + 2?",
            gold_answer="4",
        )
        d = problem.to_prompt_dict()
        assert d["id"] == "test_1"
        assert d["prompt"] == "What is 2 + 2?"
        assert d["gold_answer"] == "4"


class TestTrace:
    """Tests for Trace schema."""

    def test_create_trace(self):
        """Test basic trace creation."""
        steps = [
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
        ]
        trace = Trace(problem_id="test_1", steps=steps)

        assert trace.total_steps == 3
        assert trace.final_value == 4
        assert trace.final_step_index == 2

    def test_verify_final(self):
        """Test final answer verification."""
        trace = Trace(
            problem_id="test_1",
            steps=[
                Step(
                    index=0,
                    operation=StepOperation.ADD,
                    before_state="2 + 2",
                    after_state="4",
                    output_value=4,
                )
            ],
        )
        assert trace.verify_final(4)
        assert trace.verify_final(4.0)
        assert not trace.verify_final(5)

    def test_placeholder_map(self):
        """Test placeholder mapping."""
        steps = [
            Step(
                index=0,
                operation=StepOperation.LITERAL,
                before_state="5",
                after_state="5",
                output_value=5,
            ),
            Step(
                index=1,
                operation=StepOperation.LITERAL,
                before_state="3",
                after_state="3",
                output_value=3,
            ),
        ]
        trace = Trace(problem_id="test_1", steps=steps)

        assert trace.placeholder_map == {"x1": 5, "x2": 3}

    def test_to_natural_language(self):
        """Test natural language conversion."""
        steps = [
            Step(
                index=0,
                operation=StepOperation.ADD,
                before_state="2 + 2",
                after_state="4",
                output_value=4,
                explanation="Add 2 and 2 to get 4",
            )
        ]
        trace = Trace(problem_id="test_1", steps=steps)
        nl = trace.to_natural_language()
        assert "Add 2 and 2 to get 4" in nl


class TestStep:
    """Tests for Step schema."""

    def test_create_step(self):
        """Test basic step creation."""
        step = Step(
            index=0,
            operation=StepOperation.ADD,
            before_state="2 + 3",
            after_state="5",
            output_value=5,
        )
        assert step.output == "x1"
        assert step.output_value == 5

    def test_verify_output_numeric(self):
        """Test numeric output verification."""
        step = Step(
            index=0,
            operation=StepOperation.ADD,
            before_state="2 + 3",
            after_state="5",
            output_value=5.0,
        )
        assert step.verify_output(5.0)
        assert step.verify_output(5.0 + 1e-10)  # Within default tolerance (1e-9)
        assert not step.verify_output(5.1)

    def test_input_refs_validation(self):
        """Test that input refs must reference earlier steps."""
        with pytest.raises(ValueError):
            Step(
                index=0,
                operation=StepOperation.ADD,
                before_state="test",
                after_state="test",
                input_refs=[StepRef(step_index=0)],  # Can't reference self
                output_value=0,
            )


class TestVerificationResult:
    """Tests for VerificationResult."""

    def test_success(self):
        """Test successful verification."""
        result = VerificationResult.success(expected=4, actual=4)
        assert result.correct is True
        assert result.score == 1.0
        assert result.error_type == ErrorType.NONE

    def test_failure(self):
        """Test failed verification."""
        result = VerificationResult.failure(
            ErrorType.WRONG_ANSWER,
            "Incorrect answer",
            expected=4,
            actual=5,
        )
        assert result.correct is False
        assert result.error_type == ErrorType.WRONG_ANSWER

    def test_to_reward(self):
        """Test reward calculation."""
        success = VerificationResult.success()
        assert success.to_reward() == 1.0

        failure = VerificationResult.failure()
        assert failure.to_reward() == -1.0

        partial = VerificationResult.failure(partial_credit=0.5)
        reward = partial.to_reward(partial_weight=0.5)
        assert reward == -1.0 + (0.5 * 0.5)


class TestEpisodeRecord:
    """Tests for EpisodeRecord."""

    def test_create_episode(self):
        """Test episode record creation."""
        now = datetime.now()
        episode = EpisodeRecord(
            episode_id="ep_test",
            env_id="arithmetic.v1",
            instance_id="seed:42/diff:medium",
            domain="arithmetic",
            difficulty=DifficultyLevel.MEDIUM,
            seed=42,
            prompt="What is 2 + 2?",
            started_at=now,
            ended_at=now,
            wall_time_ms=1000,
            status=EpisodeStatus.SOLVED,
            steps_taken=1,
            invalid_actions=0,
            hints_used=0,
            optimal_steps=1,
        )
        assert episode.success is True
        assert episode.efficiency_score == 1.0

    def test_efficiency_calculation(self):
        """Test efficiency score calculation."""
        now = datetime.now()
        episode = EpisodeRecord(
            episode_id="ep_test",
            env_id="test.v1",
            instance_id="test",
            domain="test",
            difficulty=DifficultyLevel.MEDIUM,
            seed=42,
            prompt="test",
            started_at=now,
            ended_at=now,
            wall_time_ms=1000,
            status=EpisodeStatus.SOLVED,
            steps_taken=10,
            invalid_actions=0,
            hints_used=0,
            optimal_steps=5,
        )
        assert episode.efficiency_score == 0.5


class TestToolCallGrade:
    """Tests for ToolCallGrade."""

    def test_good_call(self):
        """Test good tool call grading."""
        grade = ToolCallGrade(
            tool_name="calculator",
            args={"expression": "2 + 2"},
            valid=True,
            necessary=True,
            efficient=True,
        )
        assert grade.is_good_call is True

    def test_bad_call(self):
        """Test bad tool call grading."""
        grade = ToolCallGrade(
            tool_name="calculator",
            args={},
            valid=False,
            error_message="Invalid arguments",
        )
        assert grade.is_good_call is False


class TestTraceExtended:
    """Extended tests for Trace schema."""

    def test_trace_total_cost(self):
        """Test total_cost calculation."""
        steps = [
            Step(
                index=0,
                operation=StepOperation.ADD,
                before_state="a",
                after_state="b",
                output_value=1,
                difficulty_cost=2.0,
            ),
            Step(
                index=1,
                operation=StepOperation.MULTIPLY,
                before_state="b",
                after_state="c",
                output_value=2,
                difficulty_cost=3.0,
            ),
        ]
        trace = Trace(problem_id="test", steps=steps)
        assert trace.total_cost == 5.0

    def test_trace_final_placeholder(self):
        """Test final_placeholder."""
        steps = [
            Step(
                index=0,
                operation=StepOperation.ADD,
                before_state="a",
                after_state="b",
                output_value=1,
            ),
            Step(
                index=1,
                operation=StepOperation.MULTIPLY,
                before_state="b",
                after_state="c",
                output_value=2,
            ),
        ]
        trace = Trace(problem_id="test", steps=steps, final_step_index=0)
        assert trace.final_placeholder == "x1"

    def test_trace_empty_final_placeholder(self):
        """Test final_placeholder with empty trace."""
        trace = Trace(problem_id="test", steps=[])
        assert trace.final_placeholder == ""

    def test_trace_empty_final_value(self):
        """Test final_value with empty trace."""
        trace = Trace(problem_id="test", steps=[])
        assert trace.final_value is None

    def test_trace_verify_step(self):
        """Test verify_step method."""
        steps = [
            Step(
                index=0,
                operation=StepOperation.ADD,
                before_state="a",
                after_state="b",
                output_value=42,
            ),
        ]
        trace = Trace(problem_id="test", steps=steps)
        assert trace.verify_step(0, 42)
        assert not trace.verify_step(0, 43)

    def test_trace_verify_step_out_of_range(self):
        """Test verify_step with out of range index."""
        steps = [
            Step(
                index=0,
                operation=StepOperation.ADD,
                before_state="a",
                after_state="b",
                output_value=42,
            ),
        ]
        trace = Trace(problem_id="test", steps=steps)
        with pytest.raises(IndexError):
            trace.verify_step(5, 42)

    def test_trace_get_step_values(self):
        """Test get_step_values method."""
        steps = [
            Step(
                index=0,
                operation=StepOperation.LITERAL,
                before_state="5",
                after_state="5",
                output_value=5,
            ),
            Step(
                index=1,
                operation=StepOperation.LITERAL,
                before_state="3",
                after_state="3",
                output_value=3,
            ),
        ]
        trace = Trace(problem_id="test", steps=steps)
        values = trace.get_step_values()
        assert values == [("x1", 5), ("x2", 3)]

    def test_trace_get_checkpoint_values(self):
        """Test get_checkpoint_values method."""
        steps = [
            Step(
                index=0,
                operation=StepOperation.LITERAL,
                before_state="a",
                after_state="a",
                output_value=10,
            ),
            Step(
                index=1,
                operation=StepOperation.LITERAL,
                before_state="b",
                after_state="b",
                output_value=20,
            ),
            Step(
                index=2,
                operation=StepOperation.LITERAL,
                before_state="c",
                after_state="c",
                output_value=30,
            ),
        ]
        trace = Trace(problem_id="test", steps=steps, checkpoints=[0, 2])
        values = trace.get_checkpoint_values()
        assert values == [10, 30]

    def test_trace_count_operations(self):
        """Test count_operations method."""
        steps = [
            Step(
                index=0,
                operation=StepOperation.ADD,
                before_state="a",
                after_state="b",
                output_value=1,
            ),
            Step(
                index=1,
                operation=StepOperation.ADD,
                before_state="b",
                after_state="c",
                output_value=2,
            ),
            Step(
                index=2,
                operation=StepOperation.MULTIPLY,
                before_state="c",
                after_state="d",
                output_value=3,
            ),
        ]
        trace = Trace(problem_id="test", steps=steps)
        counts = trace.count_operations()
        assert counts["add"] == 2
        assert counts["multiply"] == 1

    def test_trace_count_operations_string_op(self):
        """Test count_operations with string operations."""
        steps = [
            Step(index=0, operation="custom_op", before_state="a", after_state="b", output_value=1),
            Step(index=1, operation="custom_op", before_state="b", after_state="c", output_value=2),
        ]
        trace = Trace(problem_id="test", steps=steps)
        counts = trace.count_operations()
        assert counts["custom_op"] == 2

    def test_trace_to_placeholder_format(self):
        """Test to_placeholder_format method."""
        steps = [
            Step(
                index=0,
                operation=StepOperation.LITERAL,
                before_state="5",
                after_state="5",
                output_value=5,
            ),
            Step(
                index=1,
                operation=StepOperation.ADD,
                before_state="5 + 3",
                after_state="8",
                input_refs=[StepRef(step_index=0)],
                output_value=8,
            ),
        ]
        trace = Trace(problem_id="test", steps=steps)
        placeholder_format = trace.to_placeholder_format()
        assert "STEP 0: <x1> = 5" in placeholder_format
        assert "STEP 1: (<x1>) add = <x2>" in placeholder_format

    def test_trace_to_placeholder_format_string_op(self):
        """Test to_placeholder_format with string operation."""
        steps = [
            Step(
                index=0,
                operation="custom",
                before_state="a",
                after_state="b",
                input_refs=[],
                output_value=1,
            ),
            Step(
                index=1,
                operation="custom",
                before_state="b",
                after_state="c",
                input_refs=[StepRef(step_index=0)],
                output_value=2,
            ),
        ]
        trace = Trace(problem_id="test", steps=steps)
        placeholder_format = trace.to_placeholder_format()
        assert "custom" in placeholder_format

    def test_trace_to_natural_language_no_explanation(self):
        """Test to_natural_language without explanations."""
        steps = [
            Step(
                index=0,
                operation=StepOperation.ADD,
                before_state="2 + 2",
                after_state="4",
                output_value=4,
            ),
        ]
        trace = Trace(problem_id="test", steps=steps)
        nl = trace.to_natural_language()
        assert "2 + 2 → 4" in nl

    def test_trace_to_jsonl_steps(self):
        """Test to_jsonl_steps method."""
        steps = [
            Step(
                index=0,
                operation=StepOperation.ADD,
                before_state="2 + 2",
                after_state="4",
                output_value=4,
                rule_applied="addition",
                explanation="Add",
            ),
        ]
        trace = Trace(problem_id="test", steps=steps)
        jsonl = trace.to_jsonl_steps()
        assert len(jsonl) == 1
        assert jsonl[0]["operation"] == "add"
        assert jsonl[0]["rule"] == "addition"

    def test_trace_to_jsonl_steps_string_op(self):
        """Test to_jsonl_steps with string operation."""
        steps = [
            Step(index=0, operation="custom", before_state="a", after_state="b", output_value=1),
        ]
        trace = Trace(problem_id="test", steps=steps)
        jsonl = trace.to_jsonl_steps()
        assert jsonl[0]["operation"] == "custom"


class TestStepRefExtended:
    """Extended tests for StepRef."""

    def test_step_ref_hash(self):
        """Test StepRef hash."""
        ref1 = StepRef(step_index=0)
        ref2 = StepRef(step_index=0)
        ref3 = StepRef(step_index=1)

        assert hash(ref1) == hash(ref2)
        assert hash(ref1) != hash(ref3)

    def test_step_ref_equality(self):
        """Test StepRef equality."""
        ref1 = StepRef(step_index=0)
        ref2 = StepRef(step_index=0)
        ref3 = StepRef(step_index=1)

        assert ref1 == ref2
        assert ref1 != ref3
        assert ref1 != "not a ref"

    def test_step_ref_in_set(self):
        """Test StepRef can be used in sets."""
        refs = {StepRef(step_index=0), StepRef(step_index=0), StepRef(step_index=1)}
        assert len(refs) == 2


class TestStepExtended:
    """Extended tests for Step."""

    def test_step_verify_output_none(self):
        """Test verify_output with None expected."""
        step = Step(
            index=0,
            operation=StepOperation.ADD,
            before_state="a",
            after_state="b",
            output_value=None,
        )
        assert step.verify_output(42)  # Always true when no expected value

    def test_step_inputs_property(self):
        """Test inputs backward compatibility property."""
        step = Step(
            index=2,
            operation=StepOperation.ADD,
            before_state="a + b",
            after_state="c",
            input_refs=[StepRef(step_index=0), StepRef(step_index=1)],
            output_value=10,
        )
        assert step.inputs == ["x1", "x2"]

    def test_step_output_property(self):
        """Test output backward compatibility property."""
        step = Step(
            index=5,
            operation=StepOperation.ADD,
            before_state="a",
            after_state="b",
            output_value=1,
        )
        assert step.output == "x6"


class TestProblemExtended:
    """Extended tests for Problem."""

    def test_problem_generate_id_from_content(self):
        """Test content-based ID generation."""
        id1 = Problem.generate_id_from_content("math", "What is 2+2?")
        id2 = Problem.generate_id_from_content("math", "What is 2+2?")
        id3 = Problem.generate_id_from_content("math", "What is 3+3?")

        assert id1 == id2  # Same content = same ID
        assert id1 != id3  # Different content = different ID

    def test_problem_to_full_dict(self):
        """Test to_full_dict export."""
        problem = Problem(
            id="test_1",
            seed=42,
            domain="arithmetic",
            difficulty=DifficultyLevel.MEDIUM,
            prompt="What is 2 + 2?",
            gold_answer="4",
            expression="2 + 2",
        )
        d = problem.to_full_dict()
        assert d["id"] == "test_1"
        assert d["seed"] == 42
        assert d["difficulty"] == "medium"
        assert d["expression"] == "2 + 2"

    def test_problem_get_difficulty_profile(self):
        """Test get_difficulty_profile method."""
        problem = Problem(
            id="test_1",
            seed=42,
            domain="arithmetic",
            difficulty=DifficultyLevel.HARD,
            prompt="Test",
        )
        profile = problem.get_difficulty_profile()
        assert profile.logic_depth >= 1


class TestVerificationResultExtended:
    """Extended tests for VerificationResult."""

    def test_verification_to_feedback_dict(self):
        """Test to_feedback_dict method."""
        result = VerificationResult.failure(
            ErrorType.WRONG_ANSWER,
            "Incorrect",
            expected=4,
            actual=5,
        )
        feedback = result.to_feedback_dict()
        assert feedback["correct"] is False
        assert feedback["error_type"] == "wrong_answer"
        assert feedback["error_message"] == "Incorrect"
        assert feedback["partial_credit"] == 0.0

    def test_verification_to_reward_with_tool_penalty(self):
        """Test to_reward with tool penalty."""
        from chuk_gym_core.schemas.verification import ToolCallGrade

        grade = ToolCallGrade(
            tool_name="calc",
            args={},
            valid=True,
            penalty=0.5,
        )
        result = VerificationResult(
            correct=True,
            score=1.0,
            tool_grades=[grade],
        )
        reward = result.to_reward(tool_penalty_weight=1.0)
        assert reward == 0.5  # 1.0 - 0.5

    def test_verification_to_reward_with_policy_violation(self):
        """Test to_reward with policy violation."""
        result = VerificationResult(
            correct=True,
            score=1.0,
            tool_policy_violated=True,
        )
        reward = result.to_reward()
        assert reward == 0.5  # 1.0 - 0.5
