"""
Curriculum learning scheduler for progressive difficulty scaling.

Provides strategies for automatically adjusting difficulty based on:
- Linear progression (fixed schedule)
- Performance-based progression (adapt to success rate)
- Step-based progression (after N problems)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from chuk_gym_core.schemas.config import DifficultyLevel


@dataclass
class PerformanceMetrics:
    """Metrics tracked for curriculum decisions."""

    total_episodes: int = 0
    solved_episodes: int = 0
    total_steps: int = 0
    total_invalid: int = 0
    total_hints: int = 0
    avg_efficiency: float = 0.0

    @property
    def solve_rate(self) -> float:
        """Success rate for solved episodes."""
        if self.total_episodes == 0:
            return 0.0
        return self.solved_episodes / self.total_episodes

    @property
    def error_rate(self) -> float:
        """Rate of invalid actions."""
        total_actions = self.total_steps + self.total_invalid
        if total_actions == 0:
            return 0.0
        return self.total_invalid / total_actions

    def update(
        self,
        solved: bool,
        steps: int,
        invalid: int,
        hints: int,
        efficiency: float,
    ) -> None:
        """Update metrics with a new episode result."""
        self.total_episodes += 1
        if solved:
            self.solved_episodes += 1
        self.total_steps += steps
        self.total_invalid += invalid
        self.total_hints += hints

        # Running average for efficiency
        if self.total_episodes == 1:
            self.avg_efficiency = efficiency
        else:
            alpha = 0.1  # Exponential moving average
            self.avg_efficiency = alpha * efficiency + (1 - alpha) * self.avg_efficiency


class ProgressionStrategy(ABC):
    """Abstract base for difficulty progression strategies."""

    @abstractmethod
    def get_difficulty(
        self,
        current: DifficultyLevel,
        metrics: PerformanceMetrics,
        step: int,
    ) -> DifficultyLevel:
        """
        Determine the next difficulty level.

        Args:
            current: Current difficulty level
            metrics: Performance metrics so far
            step: Current step/episode number

        Returns:
            Next difficulty level to use
        """
        pass

    @abstractmethod
    def should_advance(
        self,
        current: DifficultyLevel,
        metrics: PerformanceMetrics,
    ) -> bool:
        """
        Check if ready to advance to next difficulty.

        Args:
            current: Current difficulty level
            metrics: Performance metrics

        Returns:
            True if should advance
        """
        pass


class LinearProgression(ProgressionStrategy):
    """
    Linear progression through difficulties.

    Advances to next difficulty every N episodes.
    """

    def __init__(
        self,
        episodes_per_level: int = 100,
        start_level: DifficultyLevel = DifficultyLevel.VERY_EASY,
    ):
        self.episodes_per_level = episodes_per_level
        self.start_level = start_level
        self._levels = list(DifficultyLevel)

    def get_difficulty(
        self,
        current: DifficultyLevel,
        metrics: PerformanceMetrics,
        step: int,
    ) -> DifficultyLevel:
        """Get difficulty based on step count."""
        level_index = step // self.episodes_per_level
        start_index = self._levels.index(self.start_level)
        target_index = min(start_index + level_index, len(self._levels) - 1)
        return self._levels[target_index]

    def should_advance(
        self,
        current: DifficultyLevel,
        metrics: PerformanceMetrics,
    ) -> bool:
        """Linear always advances on schedule."""
        return metrics.total_episodes % self.episodes_per_level == 0


class PerformanceBasedProgression(ProgressionStrategy):
    """
    Performance-based difficulty progression.

    Advances when solve rate exceeds threshold.
    Retreats when solve rate drops too low.
    """

    def __init__(
        self,
        advance_threshold: float = 0.8,
        retreat_threshold: float = 0.3,
        min_episodes: int = 20,
        window_size: int = 50,
    ):
        """
        Args:
            advance_threshold: Solve rate to trigger advancement
            retreat_threshold: Solve rate to trigger retreat
            min_episodes: Minimum episodes before considering advancement
            window_size: Episodes to consider for rolling average
        """
        self.advance_threshold = advance_threshold
        self.retreat_threshold = retreat_threshold
        self.min_episodes = min_episodes
        self.window_size = window_size
        self._levels = list(DifficultyLevel)
        self._window_results: list[bool] = []

    def get_difficulty(
        self,
        current: DifficultyLevel,
        metrics: PerformanceMetrics,
        step: int,
    ) -> DifficultyLevel:
        """Get difficulty based on performance."""
        if metrics.total_episodes < self.min_episodes:
            return current

        current_index = self._levels.index(current)

        if self.should_advance(current, metrics):
            return self._levels[min(current_index + 1, len(self._levels) - 1)]
        elif self.should_retreat(current, metrics):
            return self._levels[max(current_index - 1, 0)]

        return current

    def should_advance(
        self,
        current: DifficultyLevel,
        metrics: PerformanceMetrics,
    ) -> bool:
        """Check if performance warrants advancement."""
        if metrics.total_episodes < self.min_episodes:
            return False
        return metrics.solve_rate >= self.advance_threshold

    def should_retreat(
        self,
        current: DifficultyLevel,
        metrics: PerformanceMetrics,
    ) -> bool:
        """Check if performance warrants retreat."""
        if metrics.total_episodes < self.min_episodes:
            return False
        return metrics.solve_rate <= self.retreat_threshold

    def record_result(self, solved: bool) -> None:
        """Record episode result for windowed tracking."""
        self._window_results.append(solved)
        if len(self._window_results) > self.window_size:
            self._window_results.pop(0)

    @property
    def windowed_solve_rate(self) -> float:
        """Get solve rate over recent window."""
        if not self._window_results:
            return 0.0
        return sum(self._window_results) / len(self._window_results)


class StepBasedProgression(ProgressionStrategy):
    """
    Step-based progression with mastery requirements.

    Must solve N problems at current difficulty before advancing.
    """

    def __init__(
        self,
        required_solves: int = 10,
        max_attempts_per_level: int = 50,
    ):
        """
        Args:
            required_solves: Consecutive solves needed to advance
            max_attempts_per_level: Max attempts before forced advance
        """
        self.required_solves = required_solves
        self.max_attempts_per_level = max_attempts_per_level
        self._levels = list(DifficultyLevel)
        self._consecutive_solves = 0
        self._attempts_at_level = 0

    def get_difficulty(
        self,
        current: DifficultyLevel,
        metrics: PerformanceMetrics,
        step: int,
    ) -> DifficultyLevel:
        """Get difficulty based on mastery."""
        current_index = self._levels.index(current)

        if self.should_advance(current, metrics):
            self._consecutive_solves = 0
            self._attempts_at_level = 0
            return self._levels[min(current_index + 1, len(self._levels) - 1)]

        return current

    def should_advance(
        self,
        current: DifficultyLevel,
        metrics: PerformanceMetrics,
    ) -> bool:
        """Check if mastery achieved."""
        if self._consecutive_solves >= self.required_solves:
            return True
        if self._attempts_at_level >= self.max_attempts_per_level:
            return True  # Forced advancement
        return False

    def record_result(self, solved: bool) -> None:
        """Record episode result."""
        self._attempts_at_level += 1
        if solved:
            self._consecutive_solves += 1
        else:
            self._consecutive_solves = 0

    def reset_level(self) -> None:
        """Reset counters for new level."""
        self._consecutive_solves = 0
        self._attempts_at_level = 0


@dataclass
class CurriculumScheduler:
    """
    Main curriculum scheduler that combines strategy with state tracking.

    Usage:
        scheduler = CurriculumScheduler(
            strategy=PerformanceBasedProgression(),
            start_difficulty=DifficultyLevel.EASY,
        )

        for episode in range(1000):
            difficulty = scheduler.get_current_difficulty()
            result = run_episode(difficulty)
            scheduler.record_episode(result)
    """

    strategy: ProgressionStrategy
    start_difficulty: DifficultyLevel = DifficultyLevel.EASY
    current_difficulty: DifficultyLevel = field(init=False)
    metrics: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    step: int = 0
    history: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.current_difficulty = self.start_difficulty

    def get_current_difficulty(self) -> DifficultyLevel:
        """Get the current difficulty level."""
        return self.current_difficulty

    def record_episode(
        self,
        solved: bool,
        steps: int = 0,
        invalid: int = 0,
        hints: int = 0,
        efficiency: float = 0.0,
    ) -> DifficultyLevel:
        """
        Record an episode result and potentially adjust difficulty.

        Args:
            solved: Whether the episode was solved
            steps: Number of steps taken
            invalid: Number of invalid actions
            hints: Number of hints used
            efficiency: Efficiency score (0-1)

        Returns:
            The new (possibly adjusted) difficulty level
        """
        self.step += 1
        self.metrics.update(solved, steps, invalid, hints, efficiency)

        # Record in history
        self.history.append(
            {
                "step": self.step,
                "difficulty": self.current_difficulty.value,
                "solved": solved,
                "solve_rate": self.metrics.solve_rate,
            }
        )

        # Let strategy record if needed
        if hasattr(self.strategy, "record_result"):
            self.strategy.record_result(solved)

        # Get new difficulty
        new_difficulty = self.strategy.get_difficulty(
            self.current_difficulty,
            self.metrics,
            self.step,
        )

        if new_difficulty != self.current_difficulty:
            # Reset strategy state if needed
            if hasattr(self.strategy, "reset_level"):
                self.strategy.reset_level()
            self.current_difficulty = new_difficulty

        return self.current_difficulty

    def get_summary(self) -> dict[str, Any]:
        """Get curriculum progress summary."""
        return {
            "current_difficulty": self.current_difficulty.value,
            "total_episodes": self.metrics.total_episodes,
            "solve_rate": self.metrics.solve_rate,
            "error_rate": self.metrics.error_rate,
            "avg_efficiency": self.metrics.avg_efficiency,
        }

    def reset(self) -> None:
        """Reset scheduler to initial state."""
        self.current_difficulty = self.start_difficulty
        self.metrics = PerformanceMetrics()
        self.step = 0
        self.history = []
        if hasattr(self.strategy, "reset_level"):
            self.strategy.reset_level()
