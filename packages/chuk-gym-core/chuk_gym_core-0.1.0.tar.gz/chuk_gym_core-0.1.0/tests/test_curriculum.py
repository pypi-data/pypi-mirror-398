"""Tests for curriculum scheduler."""

import pytest

from chuk_gym_core.curriculum.scheduler import (
    CurriculumScheduler,
    LinearProgression,
    PerformanceBasedProgression,
    PerformanceMetrics,
    StepBasedProgression,
)
from chuk_gym_core.schemas.config import DifficultyLevel


class TestPerformanceMetrics:
    """Tests for PerformanceMetrics."""

    def test_initial_state(self):
        """Test initial metrics state."""
        metrics = PerformanceMetrics()
        assert metrics.total_episodes == 0
        assert metrics.solve_rate == 0.0
        assert metrics.error_rate == 0.0

    def test_update(self):
        """Test metrics update."""
        metrics = PerformanceMetrics()
        metrics.update(solved=True, steps=10, invalid=2, hints=1, efficiency=0.8)

        assert metrics.total_episodes == 1
        assert metrics.solved_episodes == 1
        assert metrics.total_steps == 10
        assert metrics.total_invalid == 2

    def test_solve_rate(self):
        """Test solve rate calculation."""
        metrics = PerformanceMetrics()
        metrics.update(solved=True, steps=10, invalid=0, hints=0, efficiency=1.0)
        metrics.update(solved=False, steps=5, invalid=0, hints=0, efficiency=0.0)

        assert metrics.solve_rate == 0.5

    def test_error_rate_calculation(self):
        """Test error rate calculation."""
        metrics = PerformanceMetrics(total_steps=80, total_invalid=20)
        assert metrics.error_rate == 0.2

    def test_error_rate_with_zero_actions(self):
        """Test error rate returns 0 when no actions."""
        metrics = PerformanceMetrics()
        assert metrics.error_rate == 0.0

    def test_efficiency_first_episode(self):
        """Test efficiency is set directly on first episode."""
        metrics = PerformanceMetrics()
        metrics.update(solved=True, steps=10, invalid=0, hints=0, efficiency=0.8)
        assert metrics.avg_efficiency == 0.8

    def test_efficiency_exponential_average(self):
        """Test efficiency uses exponential moving average."""
        metrics = PerformanceMetrics()
        metrics.update(solved=True, steps=10, invalid=0, hints=0, efficiency=1.0)
        metrics.update(solved=True, steps=10, invalid=0, hints=0, efficiency=0.5)
        # EMA: 0.1 * 0.5 + 0.9 * 1.0 = 0.95
        assert metrics.avg_efficiency == pytest.approx(0.95)


class TestLinearProgression:
    """Tests for LinearProgression strategy."""

    def test_progression(self):
        """Test linear difficulty progression."""
        strategy = LinearProgression(
            episodes_per_level=10,
            start_level=DifficultyLevel.EASY,
        )
        metrics = PerformanceMetrics()

        # Should start at easy
        level = strategy.get_difficulty(DifficultyLevel.EASY, metrics, step=0)
        assert level == DifficultyLevel.EASY

        # After 10 episodes, should advance
        level = strategy.get_difficulty(DifficultyLevel.EASY, metrics, step=10)
        assert level == DifficultyLevel.PRETTY_EASY

        # After 20 episodes, should advance again
        level = strategy.get_difficulty(DifficultyLevel.EASY, metrics, step=20)
        assert level == DifficultyLevel.MEDIUM

    def test_should_advance_on_schedule(self):
        """Test should_advance returns True when on schedule."""
        strategy = LinearProgression(episodes_per_level=10)
        metrics = PerformanceMetrics(total_episodes=10)
        assert strategy.should_advance(DifficultyLevel.EASY, metrics) is True

    def test_should_advance_not_on_schedule(self):
        """Test should_advance returns False when not on schedule."""
        strategy = LinearProgression(episodes_per_level=10)
        metrics = PerformanceMetrics(total_episodes=7)
        assert strategy.should_advance(DifficultyLevel.EASY, metrics) is False

    def test_max_level_cap(self):
        """Test difficulty is capped at maximum level."""
        strategy = LinearProgression(episodes_per_level=10)
        metrics = PerformanceMetrics()
        # Very high step should still cap at max level
        level = strategy.get_difficulty(DifficultyLevel.EASY, metrics, step=1000)
        assert level == DifficultyLevel.VERY_HARD


class TestPerformanceBasedProgression:
    """Tests for PerformanceBasedProgression strategy."""

    def test_advance_on_high_performance(self):
        """Test advancement when solve rate is high."""
        strategy = PerformanceBasedProgression(
            advance_threshold=0.8,
            min_episodes=5,
        )

        metrics = PerformanceMetrics()
        # Simulate high success rate
        for _ in range(10):
            metrics.update(solved=True, steps=5, invalid=0, hints=0, efficiency=1.0)

        assert metrics.solve_rate >= 0.8
        assert strategy.should_advance(DifficultyLevel.EASY, metrics)

    def test_no_advance_on_low_performance(self):
        """Test no advancement when solve rate is low."""
        strategy = PerformanceBasedProgression(
            advance_threshold=0.8,
            min_episodes=5,
        )

        metrics = PerformanceMetrics()
        # Simulate low success rate
        for _ in range(10):
            metrics.update(solved=False, steps=5, invalid=2, hints=0, efficiency=0.0)

        assert metrics.solve_rate < 0.8
        assert not strategy.should_advance(DifficultyLevel.EASY, metrics)

    def test_retreat_on_very_low_performance(self):
        """Test retreat when solve rate drops."""
        strategy = PerformanceBasedProgression(
            retreat_threshold=0.3,
            min_episodes=5,
        )

        metrics = PerformanceMetrics()
        # Simulate very low success rate
        for _ in range(10):
            metrics.update(solved=False, steps=5, invalid=2, hints=0, efficiency=0.0)

        assert metrics.solve_rate <= 0.3
        assert strategy.should_retreat(DifficultyLevel.MEDIUM, metrics)

    def test_get_difficulty_below_min_episodes(self):
        """Test get_difficulty returns current when below min episodes."""
        strategy = PerformanceBasedProgression(min_episodes=20)
        metrics = PerformanceMetrics(total_episodes=10, solved_episodes=10)

        result = strategy.get_difficulty(DifficultyLevel.EASY, metrics, step=10)
        assert result == DifficultyLevel.EASY

    def test_get_difficulty_advance(self):
        """Test get_difficulty advances on high solve rate."""
        strategy = PerformanceBasedProgression(advance_threshold=0.8, min_episodes=10)
        metrics = PerformanceMetrics(total_episodes=15, solved_episodes=14)

        result = strategy.get_difficulty(DifficultyLevel.EASY, metrics, step=15)
        assert result == DifficultyLevel.PRETTY_EASY

    def test_get_difficulty_retreat(self):
        """Test get_difficulty retreats on low solve rate."""
        strategy = PerformanceBasedProgression(retreat_threshold=0.3, min_episodes=10)
        metrics = PerformanceMetrics(total_episodes=15, solved_episodes=2)

        result = strategy.get_difficulty(DifficultyLevel.MEDIUM, metrics, step=15)
        assert result == DifficultyLevel.PRETTY_EASY

    def test_get_difficulty_no_change(self):
        """Test get_difficulty stays same when mid-range solve rate."""
        strategy = PerformanceBasedProgression(
            advance_threshold=0.8, retreat_threshold=0.3, min_episodes=10
        )
        metrics = PerformanceMetrics(total_episodes=15, solved_episodes=8)

        result = strategy.get_difficulty(DifficultyLevel.MEDIUM, metrics, step=15)
        assert result == DifficultyLevel.MEDIUM

    def test_no_retreat_from_lowest(self):
        """Test no retreat from lowest difficulty."""
        strategy = PerformanceBasedProgression(retreat_threshold=0.3, min_episodes=10)
        metrics = PerformanceMetrics(total_episodes=15, solved_episodes=0)

        result = strategy.get_difficulty(DifficultyLevel.VERY_EASY, metrics, step=15)
        assert result == DifficultyLevel.VERY_EASY

    def test_no_advance_from_highest(self):
        """Test no advance from highest difficulty."""
        strategy = PerformanceBasedProgression(advance_threshold=0.8, min_episodes=10)
        metrics = PerformanceMetrics(total_episodes=15, solved_episodes=15)

        result = strategy.get_difficulty(DifficultyLevel.VERY_HARD, metrics, step=15)
        assert result == DifficultyLevel.VERY_HARD

    def test_should_advance_below_min(self):
        """Test should_advance returns False below min episodes."""
        strategy = PerformanceBasedProgression(min_episodes=20)
        metrics = PerformanceMetrics(total_episodes=10, solved_episodes=10)
        assert strategy.should_advance(DifficultyLevel.EASY, metrics) is False

    def test_should_retreat_below_min(self):
        """Test should_retreat returns False below min episodes."""
        strategy = PerformanceBasedProgression(min_episodes=20)
        metrics = PerformanceMetrics(total_episodes=10, solved_episodes=0)
        assert strategy.should_retreat(DifficultyLevel.MEDIUM, metrics) is False

    def test_record_result(self):
        """Test record_result adds to window."""
        strategy = PerformanceBasedProgression(window_size=5)
        strategy.record_result(True)
        strategy.record_result(True)
        strategy.record_result(False)

        assert len(strategy._window_results) == 3
        assert strategy.windowed_solve_rate == pytest.approx(2 / 3)

    def test_windowed_solve_rate_empty(self):
        """Test windowed_solve_rate returns 0 for empty window."""
        strategy = PerformanceBasedProgression()
        assert strategy.windowed_solve_rate == 0.0

    def test_window_size_limit(self):
        """Test window is limited to window_size."""
        strategy = PerformanceBasedProgression(window_size=3)
        for _ in range(5):
            strategy.record_result(True)

        assert len(strategy._window_results) == 3


class TestStepBasedProgression:
    """Tests for StepBasedProgression strategy."""

    def test_advance_after_required_solves(self):
        """Test advancement after consecutive solves."""
        strategy = StepBasedProgression(required_solves=3)

        # Record 3 consecutive solves
        for _ in range(3):
            strategy.record_result(solved=True)

        metrics = PerformanceMetrics()
        assert strategy.should_advance(DifficultyLevel.EASY, metrics)

    def test_reset_on_failure(self):
        """Test streak reset on failure."""
        strategy = StepBasedProgression(required_solves=3)

        # Record 2 solves then fail
        strategy.record_result(solved=True)
        strategy.record_result(solved=True)
        strategy.record_result(solved=False)

        metrics = PerformanceMetrics()
        assert not strategy.should_advance(DifficultyLevel.EASY, metrics)

    def test_get_difficulty_advances(self):
        """Test get_difficulty advances when should_advance is True."""
        strategy = StepBasedProgression(required_solves=2)
        for _ in range(2):
            strategy.record_result(solved=True)
        metrics = PerformanceMetrics()

        result = strategy.get_difficulty(DifficultyLevel.EASY, metrics, step=2)
        assert result == DifficultyLevel.PRETTY_EASY
        # Check that internal counters are reset
        assert strategy._consecutive_solves == 0
        assert strategy._attempts_at_level == 0

    def test_get_difficulty_no_advance(self):
        """Test get_difficulty returns current when not advancing."""
        strategy = StepBasedProgression(required_solves=10)
        strategy.record_result(solved=True)
        metrics = PerformanceMetrics()

        result = strategy.get_difficulty(DifficultyLevel.EASY, metrics, step=1)
        assert result == DifficultyLevel.EASY

    def test_forced_advance_on_max_attempts(self):
        """Test forced advancement after max attempts."""
        strategy = StepBasedProgression(max_attempts_per_level=5)
        for _ in range(5):
            strategy.record_result(solved=False)
        metrics = PerformanceMetrics()

        assert strategy.should_advance(DifficultyLevel.EASY, metrics) is True

    def test_no_advance_past_highest(self):
        """Test no advance past highest difficulty."""
        strategy = StepBasedProgression(required_solves=1)
        strategy.record_result(solved=True)
        metrics = PerformanceMetrics()

        result = strategy.get_difficulty(DifficultyLevel.VERY_HARD, metrics, step=1)
        assert result == DifficultyLevel.VERY_HARD

    def test_reset_level(self):
        """Test reset_level resets counters."""
        strategy = StepBasedProgression()
        strategy.record_result(solved=True)
        strategy.record_result(solved=True)

        strategy.reset_level()

        assert strategy._consecutive_solves == 0
        assert strategy._attempts_at_level == 0


class TestCurriculumScheduler:
    """Tests for CurriculumScheduler."""

    def test_basic_usage(self):
        """Test basic scheduler usage."""
        scheduler = CurriculumScheduler(
            strategy=LinearProgression(episodes_per_level=5, start_level=DifficultyLevel.EASY),
            start_difficulty=DifficultyLevel.EASY,
        )

        assert scheduler.get_current_difficulty() == DifficultyLevel.EASY

        # Record some episodes
        for _ in range(5):
            scheduler.record_episode(solved=True, steps=10)

        # Should have advanced (LinearProgression advances on step count, not episode count)
        # After 5 episodes at step 5, get_difficulty with step=5 returns PRETTY_EASY
        assert scheduler.get_current_difficulty() == DifficultyLevel.PRETTY_EASY

    def test_get_summary(self):
        """Test summary generation."""
        scheduler = CurriculumScheduler(
            strategy=LinearProgression(episodes_per_level=10, start_level=DifficultyLevel.EASY),
            start_difficulty=DifficultyLevel.EASY,
        )

        for i in range(5):
            scheduler.record_episode(
                solved=i % 2 == 0,
                steps=10,
                invalid=1,
                hints=0,
                efficiency=0.8,
            )

        summary = scheduler.get_summary()
        assert summary["total_episodes"] == 5
        assert summary["current_difficulty"] == DifficultyLevel.EASY.value
        assert 0 <= summary["solve_rate"] <= 1

    def test_reset(self):
        """Test scheduler reset."""
        scheduler = CurriculumScheduler(
            strategy=LinearProgression(episodes_per_level=5),
            start_difficulty=DifficultyLevel.MEDIUM,
        )

        for _ in range(10):
            scheduler.record_episode(solved=True, steps=5)

        scheduler.reset()

        assert scheduler.get_current_difficulty() == DifficultyLevel.MEDIUM
        assert scheduler.metrics.total_episodes == 0
        assert scheduler.step == 0

    def test_record_episode_calls_strategy_record_result(self):
        """Test record_episode calls strategy.record_result if available."""
        strategy = StepBasedProgression(required_solves=3)
        scheduler = CurriculumScheduler(strategy=strategy)

        scheduler.record_episode(solved=True)
        assert strategy._consecutive_solves == 1

        scheduler.record_episode(solved=True)
        assert strategy._consecutive_solves == 2

    def test_record_episode_triggers_reset_level_on_advance(self):
        """Test reset_level is called when difficulty advances."""
        strategy = StepBasedProgression(required_solves=2)
        scheduler = CurriculumScheduler(strategy=strategy)

        scheduler.record_episode(solved=True)
        scheduler.record_episode(solved=True)

        # After advancing, reset_level should have been called
        assert strategy._consecutive_solves == 0
        assert strategy._attempts_at_level == 0

    def test_reset_calls_strategy_reset_level(self):
        """Test reset calls strategy.reset_level if available."""
        strategy = StepBasedProgression()
        scheduler = CurriculumScheduler(strategy=strategy)

        scheduler.record_episode(solved=True)
        scheduler.reset()

        assert strategy._consecutive_solves == 0
        assert strategy._attempts_at_level == 0

    def test_record_episode_updates_history(self):
        """Test record_episode updates history."""
        scheduler = CurriculumScheduler(
            strategy=LinearProgression(episodes_per_level=100),
        )

        scheduler.record_episode(solved=True)

        assert len(scheduler.history) == 1
        assert scheduler.history[0]["step"] == 1
        assert scheduler.history[0]["solved"] is True

    def test_get_summary_all_fields(self):
        """Test get_summary returns all expected fields."""
        scheduler = CurriculumScheduler(strategy=LinearProgression())
        scheduler.record_episode(solved=True, steps=10, invalid=2, hints=1, efficiency=0.8)

        summary = scheduler.get_summary()

        assert "current_difficulty" in summary
        assert "total_episodes" in summary
        assert "solve_rate" in summary
        assert "error_rate" in summary
        assert "avg_efficiency" in summary

    def test_strategy_without_record_result(self):
        """Test scheduler works with strategy without record_result."""
        scheduler = CurriculumScheduler(
            strategy=LinearProgression(episodes_per_level=5),
        )

        # Should not raise
        scheduler.record_episode(solved=True)
        assert scheduler.metrics.total_episodes == 1

    def test_strategy_without_reset_level(self):
        """Test reset works with strategy without reset_level."""
        scheduler = CurriculumScheduler(
            strategy=LinearProgression(episodes_per_level=5),
        )

        for _ in range(5):
            scheduler.record_episode(solved=True)

        # Should not raise
        scheduler.reset()
        assert scheduler.step == 0
