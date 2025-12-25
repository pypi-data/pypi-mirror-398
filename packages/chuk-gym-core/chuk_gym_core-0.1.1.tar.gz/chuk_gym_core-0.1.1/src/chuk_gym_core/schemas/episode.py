"""
Episode schema: Recording and exporting episodes for training and evaluation.

Provides unified episode recording that works for both:
- Online evaluation (benchmarking agent performance)
- Offline dataset generation (training data with teacher traces)
"""

import json
import time
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, TextIO

from pydantic import BaseModel, ConfigDict, Field, computed_field

from chuk_gym_core.schemas.config import DifficultyLevel, SolverConfig
from chuk_gym_core.schemas.trace import Step


class EpisodeStatus(str, Enum):
    """Status of a completed episode."""

    SOLVED = "solved"  # Successfully solved
    FAILED = "failed"  # Gave up or wrong final answer
    TIMEOUT = "timeout"  # Exceeded time/step limit
    ABANDONED = "abandoned"  # User quit mid-episode
    ERROR = "error"  # System error during episode


class MoveRecord(BaseModel):
    """Record of a single move in an episode for step-level analysis."""

    model_config = ConfigDict(frozen=True)

    step: int = Field(ge=0, description="Step number in episode (0-indexed)")
    action: str = Field(description="Action taken (e.g., 'place 1 5 7')")
    success: bool = Field(description="Whether the move was valid")
    advances_solution: bool = Field(
        default=True,
        description="Whether this move advances toward solution (not a backtrack)",
    )
    hint_used: bool = Field(
        default=False,
        description="Whether this move came from a hint",
    )
    timestamp_ms: int = Field(
        default=0,
        description="Milliseconds since episode start",
    )
    reward: float = Field(
        default=0.0,
        description="Reward received for this action",
    )


class TrajectoryStep(BaseModel):
    """
    Single step in a trajectory with full observation context.

    Used for dataset generation with teacher explanations.
    """

    model_config = ConfigDict(frozen=True)

    t: int = Field(ge=0, description="Step number")
    observation: Any = Field(description="State before action")
    legal_actions: list[str] | None = Field(
        default=None,
        description="Available actions at this state",
    )
    action: str = Field(description="Action taken")
    reward: float = Field(description="Reward received")
    next_observation: Any = Field(description="State after action")
    done: bool = Field(default=False, description="Whether episode ended")

    # Teacher trace (for dataset generation)
    teacher_steps: list[Step] = Field(
        default_factory=list,
        description="Step-by-step explanation of why this action is correct",
    )


class EpisodeRecord(BaseModel):
    """
    Canonical episode format for both training and evaluation.

    This is what gets exported to JSONL for dataset generation.
    Works for both math problems and logic puzzles.
    """

    model_config = ConfigDict(frozen=True)

    # Identity
    episode_id: str = Field(description="Unique episode identifier")
    env_id: str = Field(description="Environment identifier (e.g., 'arithmetic.v1', 'sudoku.v1')")
    instance_id: str = Field(description="Instance identifier (e.g., 'seed:1234/diff:medium')")

    # Problem info
    domain: str = Field(description="Domain (e.g., 'arithmetic', 'sudoku')")
    difficulty: DifficultyLevel = Field(description="Difficulty level")
    seed: int = Field(description="Reproducible puzzle seed")
    prompt: str = Field(description="Problem prompt/question")

    # Timing
    started_at: datetime = Field(description="Episode start timestamp")
    ended_at: datetime = Field(description="Episode end timestamp")
    wall_time_ms: int = Field(ge=0, description="Total wall clock time in milliseconds")

    # Outcome
    status: EpisodeStatus = Field(description="Final episode status")
    final_answer: str | None = Field(default=None, description="Final answer given")
    gold_answer: str | None = Field(default=None, description="Correct answer")

    # Raw metrics
    steps_taken: int = Field(ge=0, description="Total valid moves made")
    invalid_actions: int = Field(ge=0, description="Rejected/invalid moves")
    hints_used: int = Field(ge=0, description="Solver hints consumed")
    retries: int = Field(
        default=0,
        ge=0,
        description="Attempts on same position (backtracking indicator)",
    )

    # Ground truth reference
    optimal_steps: int | None = Field(
        default=None,
        ge=1,
        description="Minimum steps to solve (from solver)",
    )

    # Configuration used
    solver_config: SolverConfig = Field(
        default_factory=SolverConfig,
        description="Solver/hint configuration for this episode",
    )

    # Trajectory data
    trajectory: list[TrajectoryStep] = Field(
        default_factory=list,
        description="Full trajectory with observations and actions",
    )
    move_history: list[MoveRecord] = Field(
        default_factory=list,
        description="Compact move history for analysis",
    )

    # Computed metrics
    @computed_field  # type: ignore[prop-decorator]
    @property
    def success(self) -> bool:
        """Whether the puzzle was solved."""
        return self.status == EpisodeStatus.SOLVED

    @computed_field  # type: ignore[prop-decorator]
    @property
    def efficiency_score(self) -> float:
        """Ratio of optimal steps to actual steps (1.0 = optimal)."""
        if not self.success or self.optimal_steps is None or self.steps_taken == 0:
            return 0.0
        return min(1.0, self.optimal_steps / self.steps_taken)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def error_rate(self) -> float:
        """Ratio of invalid actions to total actions."""
        total = self.steps_taken + self.invalid_actions
        if total == 0:
            return 0.0
        return self.invalid_actions / total

    @computed_field  # type: ignore[prop-decorator]
    @property
    def hint_dependency(self) -> float:
        """Ratio of moves that came from hints (tool dependency)."""
        if self.steps_taken == 0:
            return 0.0
        return min(1.0, self.hints_used / self.steps_taken)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def adjusted_score(self) -> float:
        """Final score accounting for efficiency and hint penalties."""
        base_score = self.efficiency_score
        penalty = self.solver_config.hint_penalty * self.hint_dependency
        return max(0.0, base_score * (1 - penalty))

    def to_summary_dict(self) -> dict[str, Any]:
        """One-line episode summary for logging/streaming."""
        return {
            "episode_id": self.episode_id,
            "env_id": self.env_id,
            "seed": self.seed,
            "difficulty": self.difficulty.value,
            "success": self.success,
            "steps": self.steps_taken,
            "invalid": self.invalid_actions,
            "hints": self.hints_used,
            "efficiency": round(self.efficiency_score, 3),
            "time_ms": self.wall_time_ms,
        }

    def to_jsonl(self) -> str:
        """Single-line JSON for streaming output."""
        return json.dumps(self.to_summary_dict())

    def to_training_dict(self) -> dict[str, Any]:
        """Export format suitable for training data."""
        return {
            "id": self.episode_id,
            "env_id": self.env_id,
            "prompt": self.prompt,
            "trajectory": [
                {
                    "t": step.t,
                    "observation": step.observation,
                    "action": step.action,
                    "reward": step.reward,
                    "teacher_steps": [s.model_dump() for s in step.teacher_steps],
                }
                for step in self.trajectory
            ],
            "success": self.success,
            "gold_answer": self.gold_answer,
        }


class TraceEvent(BaseModel):
    """A single event in an episode trace for JSONL logging."""

    model_config = ConfigDict(frozen=True)

    type: str = Field(
        description="Event type: episode_start, observation, action, hint, episode_end"
    )
    episode_id: str = Field(description="Unique episode identifier")
    timestamp_ms: int = Field(description="Milliseconds since episode start")
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Event-specific data",
    )

    def to_jsonl(self) -> str:
        """Convert to single-line JSON for streaming."""
        return json.dumps(
            {"type": self.type, "id": self.episode_id, "ts": self.timestamp_ms, **self.data}
        )


class EpisodeTracer:
    """
    Traces complete episodes in JSONL format for offline analysis.

    Usage:
        tracer = EpisodeTracer(output_path="traces.jsonl")

        # Start episode
        tracer.start_episode(env_id="sudoku.v1", seed=42, difficulty="medium")

        # Log observations and actions
        tracer.log_observation(grid=[[...]], valid_actions=[...])
        tracer.log_action(action="place 1 5 7", success=True)
        tracer.log_hint(hint="Try row 3, column 4")

        # End episode
        tracer.end_episode(status="solved", moves=45, efficiency=0.92)
    """

    def __init__(self, output: str | Path | TextIO | None = None):
        """
        Initialize the tracer.

        Args:
            output: Output destination - file path, Path object, file handle,
                   or None for memory-only
        """
        self._output: TextIO | None = None
        self._owns_file = False
        self._events: list[TraceEvent] = []

        if output is not None:
            if isinstance(output, (str, Path)):
                self._output = open(output, "a", encoding="utf-8")
                self._owns_file = True
            else:
                self._output = output

        self._episode_id: str | None = None
        self._start_time_ns: int = 0
        self._env_id: str = ""
        self._seed: int = 0
        self._difficulty: str = ""

    def __enter__(self) -> "EpisodeTracer":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the output file if we own it."""
        if self._owns_file and self._output:
            self._output.close()
            self._output = None

    def _elapsed_ms(self) -> int:
        """Get milliseconds since episode start."""
        if self._start_time_ns == 0:
            return 0
        return int((time.time_ns() - self._start_time_ns) / 1_000_000)

    def _emit(self, event: TraceEvent) -> None:
        """Emit an event to output and memory."""
        self._events.append(event)
        if self._output:
            self._output.write(event.to_jsonl() + "\n")
            self._output.flush()

    def start_episode(
        self,
        env_id: str,
        seed: int,
        difficulty: str | DifficultyLevel,
        solver_config: SolverConfig | None = None,
        prompt: str | None = None,
        **extra: Any,
    ) -> str:
        """
        Start tracing a new episode.

        Args:
            env_id: Environment identifier
            seed: Puzzle seed
            difficulty: Difficulty level
            solver_config: Solver configuration
            prompt: Problem prompt
            **extra: Additional metadata

        Returns:
            Episode ID for reference
        """
        self._episode_id = f"ep_{uuid.uuid4().hex[:12]}"
        self._start_time_ns = time.time_ns()
        self._env_id = env_id
        self._seed = seed
        self._difficulty = (
            difficulty.value if isinstance(difficulty, DifficultyLevel) else difficulty
        )
        self._events = []

        data: dict[str, Any] = {
            "env_id": env_id,
            "seed": seed,
            "difficulty": self._difficulty,
        }
        if prompt:
            data["prompt"] = prompt
        if solver_config:
            data["solver_config"] = {
                "solver_allowed": solver_config.solver_allowed,
                "hint_budget": solver_config.hint_budget,
                "hint_penalty": solver_config.hint_penalty,
            }
        data.update(extra)

        event = TraceEvent(
            type="episode_start",
            episode_id=self._episode_id,
            timestamp_ms=0,
            data=data,
        )
        self._emit(event)

        return self._episode_id

    def log_observation(
        self,
        state: Any = None,
        valid_actions: list[str] | None = None,
        **extra: Any,
    ) -> None:
        """Log a state observation."""
        if not self._episode_id:
            return

        data: dict[str, Any] = {}
        if state is not None:
            data["state"] = state
        if valid_actions is not None:
            data["valid_actions"] = valid_actions
        data.update(extra)

        event = TraceEvent(
            type="observation",
            episode_id=self._episode_id,
            timestamp_ms=self._elapsed_ms(),
            data=data,
        )
        self._emit(event)

    def log_action(
        self,
        action: str,
        success: bool,
        reward: float = 0.0,
        **extra: Any,
    ) -> None:
        """Log an action taken."""
        if not self._episode_id:
            return

        data: dict[str, Any] = {"action": action, "success": success, "reward": reward}
        data.update(extra)

        event = TraceEvent(
            type="action",
            episode_id=self._episode_id,
            timestamp_ms=self._elapsed_ms(),
            data=data,
        )
        self._emit(event)

    def log_hint(
        self,
        hint: str,
        hints_remaining: int | None = None,
        **extra: Any,
    ) -> None:
        """Log a hint request."""
        if not self._episode_id:
            return

        data: dict[str, Any] = {"hint": hint}
        if hints_remaining is not None:
            data["hints_remaining"] = hints_remaining
        data.update(extra)

        event = TraceEvent(
            type="hint",
            episode_id=self._episode_id,
            timestamp_ms=self._elapsed_ms(),
            data=data,
        )
        self._emit(event)

    def log_teacher_step(
        self,
        step: Step,
        **extra: Any,
    ) -> None:
        """Log a teacher explanation step."""
        if not self._episode_id:
            return

        data: dict[str, Any] = {"step": step.model_dump()}
        data.update(extra)

        event = TraceEvent(
            type="teacher_step",
            episode_id=self._episode_id,
            timestamp_ms=self._elapsed_ms(),
            data=data,
        )
        self._emit(event)

    def end_episode(
        self,
        status: str | EpisodeStatus,
        moves: int = 0,
        invalid_moves: int = 0,
        hints_used: int = 0,
        optimal_steps: int | None = None,
        final_answer: str | None = None,
        **extra: Any,
    ) -> None:
        """End the current episode."""
        if not self._episode_id:
            return

        if isinstance(status, EpisodeStatus):
            status = status.value

        elapsed = self._elapsed_ms()
        efficiency = 0.0
        if status == "solved" and optimal_steps and moves > 0:
            efficiency = min(1.0, optimal_steps / moves)

        data: dict[str, Any] = {
            "status": status,
            "moves": moves,
            "invalid_moves": invalid_moves,
            "hints_used": hints_used,
            "wall_time_ms": elapsed,
        }
        if optimal_steps is not None:
            data["optimal_steps"] = optimal_steps
            data["efficiency"] = round(efficiency, 3)
        if final_answer is not None:
            data["final_answer"] = final_answer
        data.update(extra)

        event = TraceEvent(
            type="episode_end",
            episode_id=self._episode_id,
            timestamp_ms=elapsed,
            data=data,
        )
        self._emit(event)

        # Reset state
        self._episode_id = None
        self._start_time_ns = 0

    @property
    def events(self) -> list[TraceEvent]:
        """Get all events for current/last episode."""
        return self._events.copy()

    @property
    def current_episode_id(self) -> str | None:
        """Get current episode ID, or None if not in episode."""
        return self._episode_id
