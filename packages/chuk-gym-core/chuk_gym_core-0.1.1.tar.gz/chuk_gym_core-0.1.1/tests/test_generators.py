"""Tests for generators/base.py - ProblemGenerator abstract base class."""

import pytest

from chuk_gym_core.generators.base import ProblemGenerator
from chuk_gym_core.schemas.config import DifficultyLevel, ToolPolicy
from chuk_gym_core.schemas.problem import Problem
from chuk_gym_core.schemas.trace import Step, StepOperation, Trace


class ConcreteGenerator(ProblemGenerator):
    """Concrete implementation for testing."""

    @property
    def domain(self) -> str:
        return "test_generator"

    def generate(
        self,
        seed: int | None = None,
        difficulty: DifficultyLevel = DifficultyLevel.MEDIUM,
        tool_policy: ToolPolicy = ToolPolicy.ALLOWED,
    ) -> tuple[Problem, Trace]:
        if seed is None:
            seed = 12345

        problem = Problem(
            id=f"test_{difficulty.value}_{seed}",
            seed=seed,
            domain=self.domain,
            difficulty=difficulty,
            prompt=f"Test problem with seed {seed}",
            gold_answer=str(seed % 10),
            tool_policy=tool_policy,
        )

        trace = Trace(
            problem_id=problem.id,
            steps=[
                Step(
                    index=0,
                    operation=StepOperation.EVAL,
                    before_state=f"seed={seed}",
                    after_state=str(seed % 10),
                    output_value=seed % 10,
                )
            ],
        )

        return problem, trace


class LimitedDifficultyGenerator(ProblemGenerator):
    """Generator that only supports certain difficulties."""

    @property
    def domain(self) -> str:
        return "limited_generator"

    def generate(
        self,
        seed: int | None = None,
        difficulty: DifficultyLevel = DifficultyLevel.MEDIUM,
        tool_policy: ToolPolicy = ToolPolicy.ALLOWED,
    ) -> tuple[Problem, Trace]:
        if seed is None:
            seed = 12345

        problem = Problem(
            id=f"limited_{seed}",
            seed=seed,
            domain=self.domain,
            difficulty=difficulty,
            prompt="Limited problem",
        )
        trace = Trace(problem_id=problem.id, steps=[])
        return problem, trace

    def validate_difficulty(self, difficulty: DifficultyLevel) -> bool:
        return difficulty in (DifficultyLevel.EASY, DifficultyLevel.MEDIUM)

    def get_supported_difficulties(self) -> list[DifficultyLevel]:
        return [DifficultyLevel.EASY, DifficultyLevel.MEDIUM]


class TestProblemGenerator:
    """Tests for ProblemGenerator abstract base class."""

    @pytest.fixture
    def generator(self) -> ConcreteGenerator:
        return ConcreteGenerator()

    @pytest.fixture
    def limited_generator(self) -> LimitedDifficultyGenerator:
        return LimitedDifficultyGenerator()

    def test_domain_property(self, generator: ConcreteGenerator):
        """Test domain property."""
        assert generator.domain == "test_generator"

    def test_generate_with_seed(self, generator: ConcreteGenerator):
        """Test generate with specific seed."""
        problem, trace = generator.generate(seed=42)

        assert problem.seed == 42
        assert problem.id == "test_medium_42"
        assert problem.gold_answer == "2"  # 42 % 10
        assert trace.problem_id == problem.id

    def test_generate_with_difficulty(self, generator: ConcreteGenerator):
        """Test generate with specific difficulty."""
        problem, trace = generator.generate(seed=42, difficulty=DifficultyLevel.HARD)

        assert problem.difficulty == DifficultyLevel.HARD
        assert "hard" in problem.id

    def test_generate_with_tool_policy(self, generator: ConcreteGenerator):
        """Test generate with specific tool policy."""
        problem, trace = generator.generate(seed=42, tool_policy=ToolPolicy.FORBIDDEN)

        assert problem.tool_policy == ToolPolicy.FORBIDDEN

    def test_generate_without_seed(self, generator: ConcreteGenerator):
        """Test generate without seed uses random seed."""
        problem1, _ = generator.generate(seed=None)
        problem2, _ = generator.generate(seed=None)

        # Both should use default seed 12345
        assert problem1.seed == 12345
        assert problem2.seed == 12345

    def test_generate_batch(self, generator: ConcreteGenerator):
        """Test generate_batch."""
        batch = generator.generate_batch(count=5, start_seed=100)

        assert len(batch) == 5
        seeds = [p.seed for p, _ in batch]
        assert seeds == [100, 101, 102, 103, 104]

    def test_generate_batch_without_start_seed(self, generator: ConcreteGenerator):
        """Test generate_batch without start_seed."""
        batch = generator.generate_batch(count=3)

        assert len(batch) == 3
        # Seeds should be consecutive
        seeds = [p.seed for p, _ in batch]
        assert seeds[1] == seeds[0] + 1
        assert seeds[2] == seeds[1] + 1

    def test_generate_batch_with_difficulty(self, generator: ConcreteGenerator):
        """Test generate_batch with specific difficulty."""
        batch = generator.generate_batch(
            count=3, difficulty=DifficultyLevel.VERY_HARD, start_seed=1
        )

        for problem, trace in batch:
            assert problem.difficulty == DifficultyLevel.VERY_HARD

    def test_generate_batch_with_tool_policy(self, generator: ConcreteGenerator):
        """Test generate_batch with tool policy."""
        batch = generator.generate_batch(count=2, start_seed=1, tool_policy=ToolPolicy.PENALIZED)

        for problem, _ in batch:
            assert problem.tool_policy == ToolPolicy.PENALIZED

    def test_generate_iterator(self, generator: ConcreteGenerator):
        """Test generate_iterator."""
        iterator = generator.generate_iterator(start_seed=0)

        problems = []
        for i, (problem, trace) in enumerate(iterator):
            problems.append(problem)
            if i >= 4:
                break

        assert len(problems) == 5
        seeds = [p.seed for p in problems]
        assert seeds == [0, 1, 2, 3, 4]

    def test_generate_iterator_wraps_around(self, generator: ConcreteGenerator):
        """Test that iterator wraps around at max int."""
        # This tests the modulo behavior
        iterator = generator.generate_iterator(start_seed=2**31 - 2)

        problems = []
        for i, (problem, trace) in enumerate(iterator):
            problems.append(problem)
            if i >= 2:
                break

        assert problems[0].seed == 2**31 - 2
        assert problems[1].seed == 2**31 - 1
        assert problems[2].seed == 0  # Wrapped around

    def test_generate_iterator_without_start_seed(self, generator: ConcreteGenerator):
        """Test generate_iterator without start_seed."""
        iterator = generator.generate_iterator()

        problem, _ = next(iterator)
        assert problem.seed >= 0

    def test_validate_difficulty_default(self, generator: ConcreteGenerator):
        """Test default validate_difficulty returns True."""
        assert generator.validate_difficulty(DifficultyLevel.EASY) is True
        assert generator.validate_difficulty(DifficultyLevel.VERY_HARD) is True

    def test_validate_difficulty_limited(self, limited_generator: LimitedDifficultyGenerator):
        """Test limited difficulty validation."""
        assert limited_generator.validate_difficulty(DifficultyLevel.EASY) is True
        assert limited_generator.validate_difficulty(DifficultyLevel.HARD) is False

    def test_get_supported_difficulties_default(self, generator: ConcreteGenerator):
        """Test default get_supported_difficulties returns all."""
        supported = generator.get_supported_difficulties()

        assert len(supported) == 7
        assert DifficultyLevel.VERY_EASY in supported
        assert DifficultyLevel.VERY_HARD in supported

    def test_get_supported_difficulties_limited(
        self, limited_generator: LimitedDifficultyGenerator
    ):
        """Test limited get_supported_difficulties."""
        supported = limited_generator.get_supported_difficulties()

        assert len(supported) == 2
        assert DifficultyLevel.EASY in supported
        assert DifficultyLevel.MEDIUM in supported
        assert DifficultyLevel.HARD not in supported

    def test_estimate_difficulty(self, generator: ConcreteGenerator):
        """Test estimate_difficulty returns problem's difficulty."""
        problem, _ = generator.generate(seed=42, difficulty=DifficultyLevel.HARD)

        estimated = generator.estimate_difficulty(problem)

        assert estimated == DifficultyLevel.HARD

    def test_trace_has_correct_structure(self, generator: ConcreteGenerator):
        """Test that generated trace has correct structure."""
        problem, trace = generator.generate(seed=42)

        assert trace.problem_id == problem.id
        assert len(trace.steps) == 1
        assert trace.steps[0].operation == StepOperation.EVAL
        assert trace.final_value == 2  # 42 % 10


class TestGeneratorEdgeCases:
    """Edge case tests for ProblemGenerator."""

    def test_empty_batch(self):
        """Test generating empty batch."""
        generator = ConcreteGenerator()
        batch = generator.generate_batch(count=0, start_seed=1)

        assert batch == []

    def test_single_item_batch(self):
        """Test generating single item batch."""
        generator = ConcreteGenerator()
        batch = generator.generate_batch(count=1, start_seed=42)

        assert len(batch) == 1
        assert batch[0][0].seed == 42

    def test_large_batch(self):
        """Test generating large batch."""
        generator = ConcreteGenerator()
        batch = generator.generate_batch(count=100, start_seed=0)

        assert len(batch) == 100
        # Check all seeds are unique
        seeds = [p.seed for p, _ in batch]
        assert len(set(seeds)) == 100
