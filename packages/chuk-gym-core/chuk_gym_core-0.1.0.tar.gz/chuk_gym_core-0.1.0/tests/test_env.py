"""Tests for env/base.py - ReasoningEnv abstract base class."""

from datetime import datetime
from typing import Any

import pytest

from chuk_gym_core.env.base import EpisodeState, ReasoningEnv
from chuk_gym_core.schemas.config import (
    DifficultyLevel,
    DifficultyProfile,
    SolverConfig,
    ToolPolicy,
)
from chuk_gym_core.schemas.episode import EpisodeStatus
from chuk_gym_core.schemas.problem import Problem
from chuk_gym_core.schemas.trace import Step, StepOperation, Trace


class ConcreteEnv(ReasoningEnv):
    """Concrete implementation for testing."""

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._grid: list[list[int]] = [[0] * 3 for _ in range(3)]
        self._target: int = 0
        self._current_sum: int = 0

    @property
    def domain(self) -> str:
        return "test_domain"

    @property
    def constraint_types(self) -> list[str]:
        return ["test_constraint"]

    @property
    def business_analogies(self) -> list[str]:
        return ["test_analogy"]

    async def _generate_problem(
        self,
        seed: int,
        difficulty: DifficultyLevel,
    ) -> Problem:
        self._target = seed % 10 + 1
        return Problem(
            id=f"test_{seed}",
            seed=seed,
            domain=self.domain,
            difficulty=difficulty,
            prompt=f"Place numbers to sum to {self._target}",
            gold_answer=str(self._target),
        )

    async def _generate_trace(self, problem: Problem) -> Trace:
        return Trace(
            problem_id=problem.id,
            steps=[
                Step(
                    index=0,
                    operation=StepOperation.PLACE,
                    before_state="empty",
                    after_state=f"sum={self._target}",
                    output_value=self._target,
                )
            ],
        )

    async def _validate_action(self, action: str) -> tuple[bool, float, str]:
        parts = action.split()
        if len(parts) != 2 or parts[0] != "add":
            return False, 0.0, "Invalid action format. Use: add <number>"

        try:
            value = int(parts[1])
        except ValueError:
            return False, 0.0, "Invalid number"

        if value < 0 or value > 10:
            return False, 0.0, "Number must be 0-10"

        self._current_sum += value
        return True, 0.0, f"Added {value}, sum is now {self._current_sum}"

    def _is_complete(self) -> bool:
        return self._current_sum == self._target

    def _get_observation(self) -> dict[str, Any]:
        return {
            "current_sum": self._current_sum,
            "target": self._target,
            "render": f"Sum: {self._current_sum}/{self._target}",
        }

    async def _get_hint(self) -> tuple[Any, str] | None:
        remaining = self._target - self._current_sum
        if remaining > 0:
            return {"value": remaining}, f"Add {remaining} to complete"
        return None

    def _get_legal_actions(self) -> list[str] | None:
        return [f"add {i}" for i in range(11)]

    def _explain_action(self, action: str) -> Step | None:
        return Step(
            index=0,
            operation=StepOperation.PLACE,
            before_state=f"sum={self._current_sum}",
            after_state=action,
            output_value=0,
        )


class TestEpisodeState:
    """Tests for EpisodeState dataclass."""

    def test_create_episode_state(self):
        """Test basic episode state creation."""
        problem = Problem(
            id="test",
            seed=42,
            domain="test",
            difficulty=DifficultyLevel.EASY,
            prompt="Test prompt",
        )
        state = EpisodeState(problem=problem)

        assert state.problem == problem
        assert state.trace is None
        assert state.tool_calls == []
        assert state.moves == []
        assert state.trajectory == []
        assert state.steps_taken == 0
        assert state.invalid_actions == 0
        assert state.hints_used == 0
        assert state.retries == 0
        assert state.done is False
        assert state.final_result is None
        assert isinstance(state.started_at, datetime)
        assert state.last_position is None


class TestReasoningEnv:
    """Tests for ReasoningEnv abstract base class."""

    @pytest.fixture
    def env(self) -> ConcreteEnv:
        return ConcreteEnv()

    @pytest.fixture
    def env_with_config(self) -> ConcreteEnv:
        return ConcreteEnv(
            solver_config=SolverConfig.solver_assisted(budget=5, penalty=0.2),
            max_steps=100,
            step_penalty=-0.01,
            invalid_penalty=-0.5,
            hint_penalty=-0.2,
            correct_reward=1.0,
            completion_bonus=10.0,
            efficiency_multiplier=1.5,
        )

    async def test_reset_basic(self, env: ConcreteEnv):
        """Test basic reset functionality."""
        obs, info = await env.reset(seed=42, difficulty=DifficultyLevel.MEDIUM)

        assert env.state is not None
        assert env.state.problem.seed == 42
        assert env.state.problem.difficulty == DifficultyLevel.MEDIUM
        assert obs["current_sum"] == 0
        assert info["domain"] == "test_domain"

    async def test_reset_with_options(self, env: ConcreteEnv):
        """Test reset with options."""
        custom_config = SolverConfig.solver_free()
        obs, info = await env.reset(
            seed=42,
            difficulty=DifficultyLevel.EASY,
            options={
                "solver_config": custom_config,
                "tool_policy": ToolPolicy.FORBIDDEN,
            },
        )

        assert env.solver_config == custom_config
        assert env.state is not None
        assert env.state.problem.tool_policy == ToolPolicy.FORBIDDEN

    async def test_reset_random_seed(self, env: ConcreteEnv):
        """Test reset with random seed."""
        obs1, _ = await env.reset(seed=None)
        obs2, _ = await env.reset(seed=None)

        # Seeds should be different (very unlikely to be same)
        assert env.state is not None

    async def test_reset_string_difficulty(self, env: ConcreteEnv):
        """Test reset with string difficulty."""
        obs, info = await env.reset(seed=42, difficulty="medium")

        assert env.state is not None
        assert env.state.problem.difficulty == DifficultyLevel.MEDIUM

    async def test_step_valid_action(self, env: ConcreteEnv):
        """Test step with valid action."""
        await env.reset(seed=5, difficulty=DifficultyLevel.EASY)
        # seed=5 gives target=6

        obs, reward, terminated, truncated, info = await env.step("add 3")

        assert info["success"] is True
        assert obs["current_sum"] == 3
        assert terminated is False
        assert truncated is False
        assert env.state is not None
        assert env.state.steps_taken == 1

    async def test_step_invalid_action(self, env: ConcreteEnv):
        """Test step with invalid action."""
        await env.reset(seed=42, difficulty=DifficultyLevel.EASY)

        obs, reward, terminated, truncated, info = await env.step("invalid")

        assert info["success"] is False
        assert env.state is not None
        assert env.state.invalid_actions == 1
        assert reward < 0  # Should include invalid penalty

    async def test_step_completion(self, env: ConcreteEnv):
        """Test step that completes the problem."""
        await env.reset(seed=5, difficulty=DifficultyLevel.EASY)
        # seed=5 gives target=6

        obs, reward, terminated, truncated, info = await env.step("add 6")

        assert terminated is True
        assert env.state is not None
        assert env.state.done is True
        assert reward > 0  # Should include completion bonus

    async def test_step_truncation(self, env: ConcreteEnv):
        """Test step truncation at max steps."""
        env = ConcreteEnv(max_steps=3)
        await env.reset(seed=100, difficulty=DifficultyLevel.EASY)

        for i in range(3):
            obs, reward, terminated, truncated, info = await env.step("add 0")

        assert truncated is True
        assert env.state is not None
        assert env.state.done is True

    async def test_step_without_reset(self, env: ConcreteEnv):
        """Test step without reset raises error."""
        with pytest.raises(RuntimeError, match="Must call reset"):
            await env.step("add 1")

    async def test_step_after_done(self, env: ConcreteEnv):
        """Test step after episode is done raises error."""
        await env.reset(seed=5, difficulty=DifficultyLevel.EASY)
        await env.step("add 6")  # Complete the episode

        with pytest.raises(RuntimeError, match="Episode is done"):
            await env.step("add 1")

    async def test_hint_request(self, env_with_config: ConcreteEnv):
        """Test hint request."""
        await env_with_config.reset(seed=5, difficulty=DifficultyLevel.EASY)

        obs, reward, terminated, truncated, info = await env_with_config.step("hint")

        assert info["success"] is True
        assert "hint" in info
        assert env_with_config.state is not None
        assert env_with_config.state.hints_used == 1
        assert info["hints_remaining"] == 4

    async def test_hint_not_allowed(self, env: ConcreteEnv):
        """Test hint when solver not allowed."""
        env.solver_config = SolverConfig.solver_free()
        await env.reset(seed=42, difficulty=DifficultyLevel.EASY)

        obs, reward, terminated, truncated, info = await env.step("hint")

        assert info["success"] is False
        assert "not allowed" in info["message"]

    async def test_hint_budget_exhausted(self, env: ConcreteEnv):
        """Test hint when budget exhausted."""
        env.solver_config = SolverConfig.solver_assisted(budget=1)
        await env.reset(seed=42, difficulty=DifficultyLevel.EASY)

        # Use the one hint
        await env.step("hint")
        # Try again
        obs, reward, terminated, truncated, info = await env.step("hint")

        assert info["success"] is False
        assert "exhausted" in info["message"]

    async def test_get_episode_record(self, env: ConcreteEnv):
        """Test get_episode_record."""
        await env.reset(seed=99, difficulty=DifficultyLevel.MEDIUM)
        # seed=99 gives target=10 (99 % 10 + 1)
        await env.step("add 1")
        await env.step("add 2")
        # Sum is 3, target is 10, not complete

        record = env.get_episode_record()

        assert record is not None
        assert record.domain == "test_domain"
        assert record.seed == 99
        assert record.steps_taken == 2
        # Episode still in progress - status is ABANDONED since not done
        assert record.status == EpisodeStatus.ABANDONED

    async def test_get_episode_record_solved(self, env: ConcreteEnv):
        """Test get_episode_record for solved episode."""
        await env.reset(seed=5, difficulty=DifficultyLevel.EASY)
        await env.step("add 6")

        record = env.get_episode_record()

        assert record is not None
        assert record.status == EpisodeStatus.SOLVED
        assert record.success is True

    async def test_get_episode_record_timeout(self, env: ConcreteEnv):
        """Test get_episode_record for timeout."""
        env = ConcreteEnv(max_steps=2)
        await env.reset(seed=100, difficulty=DifficultyLevel.EASY)
        await env.step("add 0")
        await env.step("add 0")

        record = env.get_episode_record()

        assert record is not None
        assert record.status == EpisodeStatus.TIMEOUT

    def test_get_episode_record_no_state(self, env: ConcreteEnv):
        """Test get_episode_record with no state."""
        record = env.get_episode_record()
        assert record is None

    async def test_get_canonical_trace(self, env: ConcreteEnv):
        """Test get_canonical_trace."""
        await env.reset(seed=42, difficulty=DifficultyLevel.EASY)

        trace = env.get_canonical_trace()

        assert trace is not None
        assert trace.problem_id.startswith("test_")

    def test_get_canonical_trace_no_state(self, env: ConcreteEnv):
        """Test get_canonical_trace with no state."""
        trace = env.get_canonical_trace()
        assert trace is None

    async def test_current_problem(self, env: ConcreteEnv):
        """Test current_problem property."""
        assert env.current_problem is None

        await env.reset(seed=42, difficulty=DifficultyLevel.EASY)

        assert env.current_problem is not None
        assert env.current_problem.seed == 42

    def test_domain_property(self, env: ConcreteEnv):
        """Test domain property."""
        assert env.domain == "test_domain"

    def test_env_id_property(self, env: ConcreteEnv):
        """Test env_id property."""
        assert env.env_id == "test_domain.v1"

    async def test_render(self, env: ConcreteEnv):
        """Test render method."""
        assert env.render() is None

        await env.reset(seed=42, difficulty=DifficultyLevel.EASY)
        rendered = env.render()

        assert rendered is not None
        assert "Sum:" in rendered

    def test_close(self, env: ConcreteEnv):
        """Test close method."""
        env.close()
        assert env.state is None

    def test_unwrapped(self, env: ConcreteEnv):
        """Test unwrapped property."""
        assert env.unwrapped is env

    def test_available_difficulties(self):
        """Test available_difficulties class method."""
        difficulties = ConcreteEnv.available_difficulties()
        assert len(difficulties) == 7
        assert DifficultyLevel.EASY in difficulties
        assert DifficultyLevel.HARD in difficulties

    async def test_get_difficulty_profile(self, env: ConcreteEnv):
        """Test get_difficulty_profile."""
        profile = env.get_difficulty_profile()
        assert isinstance(profile, DifficultyProfile)

        await env.reset(seed=42, difficulty=DifficultyLevel.HARD)
        profile = env.get_difficulty_profile()
        assert profile.logic_depth >= 1

    async def test_constraint_types(self, env: ConcreteEnv):
        """Test constraint_types property."""
        assert env.constraint_types == ["test_constraint"]

    async def test_business_analogies(self, env: ConcreteEnv):
        """Test business_analogies property."""
        assert env.business_analogies == ["test_analogy"]

    async def test_optimal_steps(self, env: ConcreteEnv):
        """Test optimal_steps property."""
        assert env.optimal_steps is None

        await env.reset(seed=42, difficulty=DifficultyLevel.EASY)
        assert env.optimal_steps == 1  # Our trace has 1 step

    async def test_get_legal_actions(self, env: ConcreteEnv):
        """Test _get_legal_actions."""
        actions = env._get_legal_actions()
        assert actions is not None
        assert len(actions) == 11

    async def test_explain_action(self, env: ConcreteEnv):
        """Test _explain_action."""
        await env.reset(seed=42, difficulty=DifficultyLevel.EASY)
        step = env._explain_action("add 5")

        assert step is not None
        assert step.operation == StepOperation.PLACE

    async def test_move_recording(self, env: ConcreteEnv):
        """Test that moves are recorded."""
        await env.reset(seed=42, difficulty=DifficultyLevel.EASY)
        await env.step("add 1")
        await env.step("add 2")

        assert env.state is not None
        assert len(env.state.moves) == 2
        assert env.state.moves[0].action == "add 1"
        assert env.state.moves[1].action == "add 2"

    async def test_efficiency_bonus(self, env: ConcreteEnv):
        """Test efficiency bonus calculation."""
        env = ConcreteEnv(
            completion_bonus=10.0,
            efficiency_multiplier=2.0,
        )
        await env.reset(seed=5, difficulty=DifficultyLevel.EASY)

        # Complete in optimal steps (1 step, trace has 1 step)
        obs, reward, terminated, truncated, info = await env.step("add 6")

        # Should get full efficiency bonus
        assert reward > 10.0  # completion_bonus * efficiency * multiplier


class TestEnvWithoutHints:
    """Tests for env without hint implementation."""

    class NoHintEnv(ConcreteEnv):
        async def _get_hint(self) -> tuple[Any, str] | None:
            return None

    async def test_hint_not_available(self):
        """Test when hint implementation returns None."""
        env = self.NoHintEnv()
        await env.reset(seed=42, difficulty=DifficultyLevel.EASY)

        obs, reward, terminated, truncated, info = await env.step("hint")

        assert info["success"] is False
        assert "No hint available" in info["message"]
