"""
Base Gym-style environment for reasoning tasks.

Provides the standard RL interface:
- reset() -> (observation, info)
- step(action) -> (observation, reward, terminated, truncated, info)

Designed to integrate with:
- Standard RL frameworks (stable-baselines3, etc.)
- Gymnasium (the maintained fork of OpenAI Gym)
- Custom training loops
- Both math and puzzle domains
"""

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from chuk_gym_core.schemas.config import (
    DifficultyLevel,
    DifficultyProfile,
    SolverConfig,
    ToolPolicy,
)
from chuk_gym_core.schemas.episode import (
    EpisodeRecord,
    EpisodeStatus,
    MoveRecord,
    TrajectoryStep,
)
from chuk_gym_core.schemas.problem import Problem
from chuk_gym_core.schemas.trace import Step, Trace
from chuk_gym_core.schemas.verification import VerificationResult


@dataclass
class EpisodeState:
    """State of a single episode."""

    problem: Problem
    trace: Trace | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    moves: list[MoveRecord] = field(default_factory=list)
    trajectory: list[TrajectoryStep] = field(default_factory=list)
    steps_taken: int = 0
    invalid_actions: int = 0
    hints_used: int = 0
    retries: int = 0
    done: bool = False
    final_result: VerificationResult | None = None
    started_at: datetime = field(default_factory=datetime.now)
    last_position: tuple[Any, ...] | None = None


class ReasoningEnv(ABC):
    """
    Abstract base class for reasoning gym environments.

    Subclasses implement domain-specific problem generation,
    action handling, and verification.

    This interface is designed to work for both:
    - Math problems (arithmetic, algebra, etc.)
    - Logic puzzles (sudoku, kenken, etc.)

    Example usage:
        env = ArithmeticEnv()
        obs, info = env.reset(seed=42, difficulty=DifficultyLevel.MEDIUM)

        done = False
        while not done:
            action = agent.act(obs)
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated

        print(f"Final reward: {info.get('total_reward', 0)}")
    """

    def __init__(
        self,
        solver_config: SolverConfig | None = None,
        max_steps: int = 1000,
        step_penalty: float = 0.0,
        invalid_penalty: float = -0.5,
        hint_penalty: float = -0.1,
        correct_reward: float = 1.0,
        completion_bonus: float = 10.0,
        efficiency_multiplier: float = 1.0,
    ):
        """
        Initialize the environment.

        Args:
            solver_config: Configuration for solver/hint usage
            max_steps: Maximum steps before truncation
            step_penalty: Small penalty per step (encourages efficiency)
            invalid_penalty: Penalty for invalid actions
            hint_penalty: Penalty for using hints
            correct_reward: Reward for correct placement/step
            completion_bonus: Bonus for completing the problem
            efficiency_multiplier: Multiplier for efficiency bonus
        """
        self.solver_config = solver_config or SolverConfig()
        self.max_steps = max_steps
        self.step_penalty = step_penalty
        self.invalid_penalty = invalid_penalty
        self.hint_penalty = hint_penalty
        self.correct_reward = correct_reward
        self.completion_bonus = completion_bonus
        self.efficiency_multiplier = efficiency_multiplier

        # Current episode state
        self.state: EpisodeState | None = None
        self._rng = random.Random()
        self._step_count = 0

    # --- Abstract methods that must be implemented ---

    @property
    @abstractmethod
    def domain(self) -> str:
        """Domain identifier (e.g., 'arithmetic', 'sudoku')."""
        pass

    @property
    def env_id(self) -> str:
        """Full environment identifier (e.g., 'arithmetic.v1')."""
        return f"{self.domain}.v1"

    @abstractmethod
    async def _generate_problem(
        self,
        seed: int,
        difficulty: DifficultyLevel,
    ) -> Problem:
        """Generate a problem for this domain."""
        pass

    @abstractmethod
    async def _generate_trace(self, problem: Problem) -> Trace | None:
        """Generate the canonical solution trace for a problem."""
        pass

    @abstractmethod
    async def _validate_action(self, action: str) -> tuple[bool, float, str]:
        """
        Validate and execute an action.

        Args:
            action: Action string

        Returns:
            Tuple of (success, reward, message)
        """
        pass

    @abstractmethod
    def _is_complete(self) -> bool:
        """Check if the problem is completely solved."""
        pass

    @abstractmethod
    def _get_observation(self) -> dict[str, Any]:
        """Get the current observation."""
        pass

    # --- Optional methods that can be overridden ---

    @property
    def constraint_types(self) -> list[str]:
        """Constraint types demonstrated by this domain."""
        return []

    @property
    def business_analogies(self) -> list[str]:
        """Real-world problems this domain models."""
        return []

    def get_difficulty_profile(self) -> DifficultyProfile:
        """Get difficulty profile for current problem."""
        if self.state and self.state.problem:
            return self.state.problem.get_difficulty_profile()
        return DifficultyProfile()

    async def _get_hint(self) -> tuple[Any, str] | None:
        """Get a hint for the next move. Override in subclasses."""
        return None

    def _get_legal_actions(self) -> list[str] | None:
        """Get list of legal actions. Override if enumerable."""
        return None

    def _explain_action(self, action: str) -> Step | None:
        """Generate a teacher explanation for an action."""
        return None

    @property
    def optimal_steps(self) -> int | None:
        """Minimum steps to solve (from trace)."""
        if self.state and self.state.trace:
            return self.state.trace.total_steps
        return None

    # --- Core Gym interface ---

    async def reset(
        self,
        seed: int | None = None,
        difficulty: DifficultyLevel | str | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """
        Reset the environment and generate a new problem.

        Args:
            seed: Random seed for reproducibility (None = random)
            difficulty: Difficulty level (None = random)
            options: Additional options (e.g., tool_policy override)

        Returns:
            Tuple of (observation, info)
        """
        # Handle seed
        if seed is None:
            seed = random.randint(0, 2**31 - 1)
        self._rng.seed(seed)

        # Handle difficulty
        if difficulty is None:
            difficulty = self._rng.choice(list(DifficultyLevel))
        elif isinstance(difficulty, str):
            difficulty = DifficultyLevel(difficulty)

        # Apply options
        if options and "solver_config" in options:
            self.solver_config = options["solver_config"]

        # Generate problem
        problem = await self._generate_problem(seed, difficulty)

        # Apply tool policy override from options
        if options and "tool_policy" in options:
            problem.tool_policy = ToolPolicy(options["tool_policy"])

        # Generate trace for verification
        trace = await self._generate_trace(problem)

        # Initialize episode state
        self.state = EpisodeState(
            problem=problem,
            trace=trace,
            started_at=datetime.now(),
        )
        self._step_count = 0

        return self._get_observation(), self._get_info()

    async def step(
        self,
        action: str,
    ) -> tuple[dict[str, Any], float, bool, bool, dict[str, Any]]:
        """
        Take an action in the environment.

        Args:
            action: Action string (format depends on domain)

        Returns:
            Tuple of (observation, reward, terminated, truncated, info)
        """
        if self.state is None:
            raise RuntimeError("Must call reset() before step()")

        if self.state.done:
            raise RuntimeError("Episode is done. Call reset() to start new episode.")

        self._step_count += 1
        action = action.strip()

        # Parse special commands
        if action.lower().startswith("hint"):
            return await self._handle_hint()

        # Validate and execute action
        success, reward, message = await self._validate_action(action)

        # Track metrics
        if success:
            self.state.steps_taken += 1
            reward += self.correct_reward
        else:
            self.state.invalid_actions += 1
            reward += self.invalid_penalty

        # Apply step penalty
        reward += self.step_penalty

        # Record move
        self.state.moves.append(
            MoveRecord(
                step=len(self.state.moves),
                action=action,
                success=success,
                timestamp_ms=int((datetime.now() - self.state.started_at).total_seconds() * 1000),
                reward=reward,
            )
        )

        # Check completion
        terminated = False
        if self._is_complete():
            terminated = True
            self.state.done = True

            # Calculate completion bonus with efficiency
            optimal = self.optimal_steps
            if optimal and self.state.steps_taken > 0:
                efficiency = min(1.0, optimal / self.state.steps_taken)
            else:
                efficiency = 1.0

            bonus = self.completion_bonus * efficiency * self.efficiency_multiplier
            reward += bonus

        # Check truncation
        truncated = self._step_count >= self.max_steps
        if truncated:
            self.state.done = True

        info = {
            "action": action,
            "success": success,
            "message": message,
            "steps_taken": self.state.steps_taken,
            "invalid_actions": self.state.invalid_actions,
            "hints_used": self.state.hints_used,
        }

        return self._get_observation(), reward, terminated, truncated, info

    async def _handle_hint(
        self,
    ) -> tuple[dict[str, Any], float, bool, bool, dict[str, Any]]:
        """Handle a hint request."""
        assert self.state is not None

        # Check if hints allowed
        if not self.solver_config.solver_allowed:
            return (
                self._get_observation(),
                self.invalid_penalty,
                False,
                False,
                {"success": False, "message": "Hints not allowed"},
            )

        # Check budget
        if self.state.hints_used >= self.solver_config.hint_budget:
            return (
                self._get_observation(),
                self.invalid_penalty,
                False,
                False,
                {"success": False, "message": "Hint budget exhausted"},
            )

        # Get hint
        hint_result = await self._get_hint()
        if hint_result is None:
            return (
                self._get_observation(),
                0.0,
                False,
                False,
                {"success": False, "message": "No hint available"},
            )

        hint_data, hint_message = hint_result
        self.state.hints_used += 1

        return (
            self._get_observation(),
            self.hint_penalty,
            False,
            False,
            {
                "success": True,
                "hint": hint_message,
                "hint_data": hint_data,
                "hints_remaining": self.solver_config.hint_budget - self.state.hints_used,
            },
        )

    def _get_info(self) -> dict[str, Any]:
        """Get additional info about the environment state."""
        if self.state is None:
            return {}

        profile = self.get_difficulty_profile()
        return {
            "env_id": self.env_id,
            "domain": self.domain,
            "seed": self.state.problem.seed,
            "difficulty": self.state.problem.difficulty.value,
            "optimal_steps": self.optimal_steps,
            "difficulty_profile": {
                "logic_depth": profile.logic_depth,
                "branching_factor": profile.branching_factor,
                "state_observability": profile.state_observability,
                "constraint_density": profile.constraint_density,
            },
            "constraint_types": self.constraint_types,
            "solver_config": {
                "solver_allowed": self.solver_config.solver_allowed,
                "hint_budget": self.solver_config.hint_budget,
                "hint_penalty": self.solver_config.hint_penalty,
            },
        }

    def render(self, mode: str = "ansi") -> str | None:
        """Render the environment state."""
        if self.state is None:
            return None
        obs = self._get_observation()
        render_val = obs.get("render")
        if render_val is not None:
            return str(render_val)
        return str(obs)

    def close(self) -> None:
        """Clean up environment resources."""
        self.state = None

    # --- Episode recording ---

    def get_episode_record(self) -> EpisodeRecord | None:
        """Get the complete episode record for export."""
        if self.state is None:
            return None

        status = EpisodeStatus.ABANDONED
        if self.state.done:
            if self._is_complete():
                status = EpisodeStatus.SOLVED
            elif self._step_count >= self.max_steps:
                status = EpisodeStatus.TIMEOUT
            else:
                status = EpisodeStatus.FAILED

        ended_at = datetime.now()
        wall_time_ms = int((ended_at - self.state.started_at).total_seconds() * 1000)

        return EpisodeRecord(
            episode_id=f"ep_{self.state.problem.id}_{self.state.problem.seed}",
            env_id=self.env_id,
            instance_id=f"seed:{self.state.problem.seed}/diff:{self.state.problem.difficulty.value}",
            domain=self.domain,
            difficulty=self.state.problem.difficulty,
            seed=self.state.problem.seed,
            prompt=self.state.problem.prompt,
            started_at=self.state.started_at,
            ended_at=ended_at,
            wall_time_ms=wall_time_ms,
            status=status,
            final_answer=None,  # Subclasses can override
            gold_answer=self.state.problem.gold_answer,
            steps_taken=self.state.steps_taken,
            invalid_actions=self.state.invalid_actions,
            hints_used=self.state.hints_used,
            retries=self.state.retries,
            optimal_steps=self.optimal_steps,
            solver_config=self.solver_config,
            move_history=self.state.moves,
            trajectory=self.state.trajectory,
        )

    def get_canonical_trace(self) -> Trace | None:
        """Get the step-by-step solution trace (for dataset generation)."""
        if self.state:
            return self.state.trace
        return None

    # --- Properties ---

    @property
    def current_problem(self) -> Problem | None:
        """Get the current problem (if any)."""
        return self.state.problem if self.state else None

    @property
    def unwrapped(self) -> "ReasoningEnv":
        """Return the base environment (Gymnasium compatibility)."""
        return self

    # --- Class methods ---

    @classmethod
    def available_difficulties(cls) -> list[DifficultyLevel]:
        """Get list of supported difficulty levels."""
        return list(DifficultyLevel)
