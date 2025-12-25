"""Tests for episode.py - EpisodeTracer and related classes."""

import json
import time
from datetime import datetime
from io import StringIO
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from chuk_gym_core.schemas.config import DifficultyLevel, SolverConfig
from chuk_gym_core.schemas.episode import (
    EpisodeRecord,
    EpisodeStatus,
    EpisodeTracer,
    MoveRecord,
    TraceEvent,
    TrajectoryStep,
)
from chuk_gym_core.schemas.trace import Step, StepOperation


class TestMoveRecord:
    """Tests for MoveRecord."""

    def test_create_move_record(self):
        """Test basic move record creation."""
        move = MoveRecord(
            step=0,
            action="place 1 5 7",
            success=True,
            advances_solution=True,
            hint_used=False,
            timestamp_ms=100,
            reward=1.0,
        )

        assert move.step == 0
        assert move.action == "place 1 5 7"
        assert move.success is True
        assert move.advances_solution is True
        assert move.hint_used is False
        assert move.timestamp_ms == 100
        assert move.reward == 1.0

    def test_move_record_defaults(self):
        """Test move record default values."""
        move = MoveRecord(step=0, action="test", success=True)

        assert move.advances_solution is True
        assert move.hint_used is False
        assert move.timestamp_ms == 0
        assert move.reward == 0.0

    def test_move_record_frozen(self):
        """Test that move record is frozen."""
        move = MoveRecord(step=0, action="test", success=True)

        with pytest.raises(Exception):
            move.step = 1


class TestTrajectoryStep:
    """Tests for TrajectoryStep."""

    def test_create_trajectory_step(self):
        """Test basic trajectory step creation."""
        step = TrajectoryStep(
            t=0,
            observation={"grid": [[1, 2], [3, 4]]},
            legal_actions=["place 1", "place 2"],
            action="place 1",
            reward=1.0,
            next_observation={"grid": [[1, 2], [3, 5]]},
            done=False,
        )

        assert step.t == 0
        assert step.observation == {"grid": [[1, 2], [3, 4]]}
        assert step.legal_actions == ["place 1", "place 2"]
        assert step.action == "place 1"
        assert step.reward == 1.0
        assert step.done is False

    def test_trajectory_step_with_teacher_steps(self):
        """Test trajectory step with teacher steps."""
        teacher = Step(
            index=0,
            operation=StepOperation.PLACE,
            before_state="empty",
            after_state="placed",
            output_value=1,
        )

        step = TrajectoryStep(
            t=0,
            observation={},
            action="place 1",
            reward=1.0,
            next_observation={},
            teacher_steps=[teacher],
        )

        assert len(step.teacher_steps) == 1
        assert step.teacher_steps[0].output_value == 1

    def test_trajectory_step_frozen(self):
        """Test that trajectory step is frozen."""
        step = TrajectoryStep(
            t=0,
            observation={},
            action="test",
            reward=0.0,
            next_observation={},
        )

        with pytest.raises(Exception):
            step.t = 1


class TestTraceEvent:
    """Tests for TraceEvent."""

    def test_create_trace_event(self):
        """Test basic trace event creation."""
        event = TraceEvent(
            type="action",
            episode_id="ep_123",
            timestamp_ms=500,
            data={"action": "test", "success": True},
        )

        assert event.type == "action"
        assert event.episode_id == "ep_123"
        assert event.timestamp_ms == 500
        assert event.data["action"] == "test"

    def test_trace_event_to_jsonl(self):
        """Test trace event to JSONL conversion."""
        event = TraceEvent(
            type="action",
            episode_id="ep_123",
            timestamp_ms=500,
            data={"action": "test", "reward": 1.0},
        )

        jsonl = event.to_jsonl()
        data = json.loads(jsonl)

        assert data["type"] == "action"
        assert data["id"] == "ep_123"
        assert data["ts"] == 500
        assert data["action"] == "test"
        assert data["reward"] == 1.0

    def test_trace_event_frozen(self):
        """Test that trace event is frozen."""
        event = TraceEvent(
            type="action",
            episode_id="ep_123",
            timestamp_ms=500,
        )

        with pytest.raises(Exception):
            event.type = "observation"


class TestEpisodeRecord:
    """Tests for EpisodeRecord."""

    @pytest.fixture
    def episode(self) -> EpisodeRecord:
        now = datetime.now()
        return EpisodeRecord(
            episode_id="ep_test",
            env_id="test.v1",
            instance_id="seed:42/diff:medium",
            domain="test",
            difficulty=DifficultyLevel.MEDIUM,
            seed=42,
            prompt="Test problem",
            started_at=now,
            ended_at=now,
            wall_time_ms=1000,
            status=EpisodeStatus.SOLVED,
            final_answer="42",
            gold_answer="42",
            steps_taken=10,
            invalid_actions=2,
            hints_used=1,
            optimal_steps=5,
        )

    def test_success_property(self, episode: EpisodeRecord):
        """Test success computed property."""
        assert episode.success is True

        failed = EpisodeRecord(
            episode_id="ep_fail",
            env_id="test.v1",
            instance_id="test",
            domain="test",
            difficulty=DifficultyLevel.EASY,
            seed=1,
            prompt="Test",
            started_at=datetime.now(),
            ended_at=datetime.now(),
            wall_time_ms=500,
            status=EpisodeStatus.FAILED,
            steps_taken=5,
            invalid_actions=0,
            hints_used=0,
        )
        assert failed.success is False

    def test_efficiency_score(self, episode: EpisodeRecord):
        """Test efficiency_score computed property."""
        assert episode.efficiency_score == 0.5  # 5/10

    def test_efficiency_score_no_optimal(self):
        """Test efficiency_score when optimal_steps is None."""
        episode = EpisodeRecord(
            episode_id="ep_test",
            env_id="test.v1",
            instance_id="test",
            domain="test",
            difficulty=DifficultyLevel.EASY,
            seed=1,
            prompt="Test",
            started_at=datetime.now(),
            ended_at=datetime.now(),
            wall_time_ms=500,
            status=EpisodeStatus.SOLVED,
            steps_taken=10,
            invalid_actions=0,
            hints_used=0,
            optimal_steps=None,
        )
        assert episode.efficiency_score == 0.0

    def test_efficiency_score_no_steps(self):
        """Test efficiency_score when steps_taken is 0."""
        episode = EpisodeRecord(
            episode_id="ep_test",
            env_id="test.v1",
            instance_id="test",
            domain="test",
            difficulty=DifficultyLevel.EASY,
            seed=1,
            prompt="Test",
            started_at=datetime.now(),
            ended_at=datetime.now(),
            wall_time_ms=500,
            status=EpisodeStatus.SOLVED,
            steps_taken=0,
            invalid_actions=0,
            hints_used=0,
            optimal_steps=5,
        )
        assert episode.efficiency_score == 0.0

    def test_error_rate(self, episode: EpisodeRecord):
        """Test error_rate computed property."""
        assert episode.error_rate == pytest.approx(2 / 12)  # 2 / (10 + 2)

    def test_error_rate_no_actions(self):
        """Test error_rate when no actions taken."""
        episode = EpisodeRecord(
            episode_id="ep_test",
            env_id="test.v1",
            instance_id="test",
            domain="test",
            difficulty=DifficultyLevel.EASY,
            seed=1,
            prompt="Test",
            started_at=datetime.now(),
            ended_at=datetime.now(),
            wall_time_ms=500,
            status=EpisodeStatus.FAILED,
            steps_taken=0,
            invalid_actions=0,
            hints_used=0,
        )
        assert episode.error_rate == 0.0

    def test_hint_dependency(self, episode: EpisodeRecord):
        """Test hint_dependency computed property."""
        assert episode.hint_dependency == 0.1  # 1/10

    def test_hint_dependency_no_steps(self):
        """Test hint_dependency when no steps taken."""
        episode = EpisodeRecord(
            episode_id="ep_test",
            env_id="test.v1",
            instance_id="test",
            domain="test",
            difficulty=DifficultyLevel.EASY,
            seed=1,
            prompt="Test",
            started_at=datetime.now(),
            ended_at=datetime.now(),
            wall_time_ms=500,
            status=EpisodeStatus.FAILED,
            steps_taken=0,
            invalid_actions=0,
            hints_used=5,
        )
        assert episode.hint_dependency == 0.0

    def test_adjusted_score(self, episode: EpisodeRecord):
        """Test adjusted_score computed property."""
        # efficiency_score = 0.5, hint_dependency = 0.1, hint_penalty = 0.0
        assert episode.adjusted_score == 0.5

    def test_adjusted_score_with_penalty(self):
        """Test adjusted_score with hint penalty."""
        episode = EpisodeRecord(
            episode_id="ep_test",
            env_id="test.v1",
            instance_id="test",
            domain="test",
            difficulty=DifficultyLevel.EASY,
            seed=1,
            prompt="Test",
            started_at=datetime.now(),
            ended_at=datetime.now(),
            wall_time_ms=500,
            status=EpisodeStatus.SOLVED,
            steps_taken=10,
            invalid_actions=0,
            hints_used=5,
            optimal_steps=5,
            solver_config=SolverConfig(hint_penalty=0.1),
        )
        # efficiency = 0.5, hint_dependency = 0.5, penalty = 0.1 * 0.5 = 0.05
        # adjusted = 0.5 * (1 - 0.05) = 0.475
        assert episode.adjusted_score == pytest.approx(0.475)

    def test_to_summary_dict(self, episode: EpisodeRecord):
        """Test to_summary_dict."""
        summary = episode.to_summary_dict()

        assert summary["episode_id"] == "ep_test"
        assert summary["env_id"] == "test.v1"
        assert summary["seed"] == 42
        assert summary["difficulty"] == "medium"
        assert summary["success"] is True
        assert summary["steps"] == 10
        assert summary["invalid"] == 2
        assert summary["hints"] == 1
        assert summary["efficiency"] == 0.5
        assert summary["time_ms"] == 1000

    def test_to_jsonl(self, episode: EpisodeRecord):
        """Test to_jsonl."""
        jsonl = episode.to_jsonl()
        data = json.loads(jsonl)

        assert data["episode_id"] == "ep_test"
        assert data["success"] is True

    def test_to_training_dict(self, episode: EpisodeRecord):
        """Test to_training_dict."""
        training = episode.to_training_dict()

        assert training["id"] == "ep_test"
        assert training["env_id"] == "test.v1"
        assert training["prompt"] == "Test problem"
        assert training["success"] is True
        assert training["gold_answer"] == "42"

    def test_episode_record_frozen(self, episode: EpisodeRecord):
        """Test that episode record is frozen."""
        with pytest.raises(Exception):
            episode.episode_id = "different"


class TestEpisodeTracer:
    """Tests for EpisodeTracer."""

    def test_init_memory_only(self):
        """Test initialization without output."""
        tracer = EpisodeTracer()
        assert tracer._output is None
        assert tracer.current_episode_id is None

    def test_init_with_string_path(self):
        """Test initialization with string path."""
        with NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = f.name

        tracer = EpisodeTracer(path)
        tracer.close()

        Path(path).unlink()

    def test_init_with_path_object(self):
        """Test initialization with Path object."""
        with NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = Path(f.name)

        tracer = EpisodeTracer(path)
        tracer.close()

        path.unlink()

    def test_init_with_file_handle(self):
        """Test initialization with file handle."""
        output = StringIO()
        tracer = EpisodeTracer(output)
        tracer.close()

    def test_context_manager(self):
        """Test context manager usage."""
        output = StringIO()

        with EpisodeTracer(output) as tracer:
            tracer.start_episode("test.v1", seed=42, difficulty="easy")
            tracer.end_episode("solved")

        output.seek(0)
        lines = output.readlines()
        assert len(lines) == 2  # start + end

    def test_start_episode(self):
        """Test start_episode."""
        output = StringIO()
        tracer = EpisodeTracer(output)

        episode_id = tracer.start_episode(
            env_id="test.v1",
            seed=42,
            difficulty=DifficultyLevel.MEDIUM,
            prompt="Test problem",
        )

        assert episode_id.startswith("ep_")
        assert tracer.current_episode_id == episode_id

        output.seek(0)
        data = json.loads(output.readline())

        assert data["type"] == "episode_start"
        assert data["env_id"] == "test.v1"
        assert data["seed"] == 42
        assert data["difficulty"] == "medium"
        assert data["prompt"] == "Test problem"

        tracer.close()

    def test_start_episode_with_solver_config(self):
        """Test start_episode with solver config."""
        output = StringIO()
        tracer = EpisodeTracer(output)

        config = SolverConfig.solver_assisted(budget=10, penalty=0.1)
        tracer.start_episode(
            env_id="test.v1",
            seed=42,
            difficulty="easy",
            solver_config=config,
        )

        output.seek(0)
        data = json.loads(output.readline())

        assert data["solver_config"]["solver_allowed"] is True
        assert data["solver_config"]["hint_budget"] == 10
        assert data["solver_config"]["hint_penalty"] == 0.1

        tracer.close()

    def test_start_episode_with_extra(self):
        """Test start_episode with extra data."""
        output = StringIO()
        tracer = EpisodeTracer(output)

        tracer.start_episode(
            env_id="test.v1",
            seed=42,
            difficulty="easy",
            custom_field="custom_value",
        )

        output.seek(0)
        data = json.loads(output.readline())

        assert data["custom_field"] == "custom_value"

        tracer.close()

    def test_log_observation(self):
        """Test log_observation."""
        output = StringIO()
        tracer = EpisodeTracer(output)
        tracer.start_episode("test.v1", seed=42, difficulty="easy")

        tracer.log_observation(
            state={"grid": [[1, 2], [3, 4]]},
            valid_actions=["a", "b", "c"],
        )

        output.seek(0)
        output.readline()  # Skip start event
        data = json.loads(output.readline())

        assert data["type"] == "observation"
        assert data["state"] == {"grid": [[1, 2], [3, 4]]}
        assert data["valid_actions"] == ["a", "b", "c"]

        tracer.close()

    def test_log_observation_no_episode(self):
        """Test log_observation without active episode."""
        tracer = EpisodeTracer()
        tracer.log_observation(state={})  # Should not raise
        assert tracer.events == []

    def test_log_action(self):
        """Test log_action."""
        output = StringIO()
        tracer = EpisodeTracer(output)
        tracer.start_episode("test.v1", seed=42, difficulty="easy")

        tracer.log_action(action="place 1 5 7", success=True, reward=1.0)

        output.seek(0)
        output.readline()  # Skip start event
        data = json.loads(output.readline())

        assert data["type"] == "action"
        assert data["action"] == "place 1 5 7"
        assert data["success"] is True
        assert data["reward"] == 1.0

        tracer.close()

    def test_log_action_no_episode(self):
        """Test log_action without active episode."""
        tracer = EpisodeTracer()
        tracer.log_action(action="test", success=True)  # Should not raise
        assert tracer.events == []

    def test_log_hint(self):
        """Test log_hint."""
        output = StringIO()
        tracer = EpisodeTracer(output)
        tracer.start_episode("test.v1", seed=42, difficulty="easy")

        tracer.log_hint(hint="Try row 3, column 4", hints_remaining=5)

        output.seek(0)
        output.readline()  # Skip start event
        data = json.loads(output.readline())

        assert data["type"] == "hint"
        assert data["hint"] == "Try row 3, column 4"
        assert data["hints_remaining"] == 5

        tracer.close()

    def test_log_hint_no_episode(self):
        """Test log_hint without active episode."""
        tracer = EpisodeTracer()
        tracer.log_hint(hint="test")  # Should not raise
        assert tracer.events == []

    def test_log_teacher_step(self):
        """Test log_teacher_step."""
        output = StringIO()
        tracer = EpisodeTracer(output)
        tracer.start_episode("test.v1", seed=42, difficulty="easy")

        step = Step(
            index=0,
            operation=StepOperation.PLACE,
            before_state="empty",
            after_state="placed",
            output_value=7,
        )
        tracer.log_teacher_step(step)

        output.seek(0)
        output.readline()  # Skip start event
        data = json.loads(output.readline())

        assert data["type"] == "teacher_step"
        assert data["step"]["index"] == 0
        assert data["step"]["operation"] == "place"

        tracer.close()

    def test_log_teacher_step_no_episode(self):
        """Test log_teacher_step without active episode."""
        tracer = EpisodeTracer()
        step = Step(
            index=0,
            operation=StepOperation.PLACE,
            before_state="a",
            after_state="b",
            output_value=1,
        )
        tracer.log_teacher_step(step)  # Should not raise
        assert tracer.events == []

    def test_end_episode(self):
        """Test end_episode."""
        output = StringIO()
        tracer = EpisodeTracer(output)
        tracer.start_episode("test.v1", seed=42, difficulty="easy")

        # Small delay to ensure elapsed time
        time.sleep(0.01)

        tracer.end_episode(
            status=EpisodeStatus.SOLVED,
            moves=10,
            invalid_moves=2,
            hints_used=1,
            optimal_steps=5,
            final_answer="42",
        )

        assert tracer.current_episode_id is None

        output.seek(0)
        output.readline()  # Skip start event
        data = json.loads(output.readline())

        assert data["type"] == "episode_end"
        assert data["status"] == "solved"
        assert data["moves"] == 10
        assert data["invalid_moves"] == 2
        assert data["hints_used"] == 1
        assert data["optimal_steps"] == 5
        assert data["efficiency"] == 0.5
        assert data["final_answer"] == "42"
        assert data["wall_time_ms"] >= 10

        tracer.close()

    def test_end_episode_string_status(self):
        """Test end_episode with string status."""
        output = StringIO()
        tracer = EpisodeTracer(output)
        tracer.start_episode("test.v1", seed=42, difficulty="easy")
        tracer.end_episode(status="failed")

        output.seek(0)
        output.readline()
        data = json.loads(output.readline())

        assert data["status"] == "failed"

        tracer.close()

    def test_end_episode_no_episode(self):
        """Test end_episode without active episode."""
        tracer = EpisodeTracer()
        tracer.end_episode(status="solved")  # Should not raise
        assert tracer.events == []

    def test_events_property(self):
        """Test events property returns copy."""
        tracer = EpisodeTracer()
        tracer.start_episode("test.v1", seed=42, difficulty="easy")

        events = tracer.events
        assert len(events) == 1

        # Modify returned list
        events.append(None)

        # Original should be unchanged
        assert len(tracer.events) == 1

        tracer.close()

    def test_elapsed_ms_no_episode(self):
        """Test _elapsed_ms without active episode."""
        tracer = EpisodeTracer()
        assert tracer._elapsed_ms() == 0

    def test_close_owns_file(self):
        """Test close when tracer owns file."""
        with NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = f.name

        tracer = EpisodeTracer(path)
        tracer.start_episode("test.v1", seed=42, difficulty="easy")
        tracer.close()

        # File should be closed
        assert tracer._output is None

        Path(path).unlink()

    def test_close_does_not_own_file(self):
        """Test close when tracer doesn't own file."""
        output = StringIO()
        tracer = EpisodeTracer(output)
        tracer.close()

        # StringIO should not be closed
        output.write("test")  # Should not raise

    def test_full_episode_workflow(self):
        """Test complete episode workflow."""
        output = StringIO()

        with EpisodeTracer(output) as tracer:
            ep_id = tracer.start_episode(
                env_id="sudoku.v1",
                seed=42,
                difficulty=DifficultyLevel.MEDIUM,
                prompt="Solve this puzzle",
            )

            tracer.log_observation(state={"grid": []}, valid_actions=["place 1 1 5"])
            tracer.log_action(action="place 1 1 5", success=True, reward=1.0)
            tracer.log_observation(state={"grid": [[5]]})
            tracer.log_hint(hint="Try cell 2,2", hints_remaining=4)
            tracer.log_action(action="place 2 2 3", success=True, reward=1.0)
            tracer.end_episode(
                status="solved",
                moves=2,
                invalid_moves=0,
                hints_used=1,
                optimal_steps=2,
            )

        output.seek(0)
        lines = output.readlines()

        # Should have: start, obs, action, obs, hint, action, end = 7 events
        assert len(lines) == 7

        # Verify event types
        events = [json.loads(line) for line in lines]
        assert events[0]["type"] == "episode_start"
        assert events[1]["type"] == "observation"
        assert events[2]["type"] == "action"
        assert events[3]["type"] == "observation"
        assert events[4]["type"] == "hint"
        assert events[5]["type"] == "action"
        assert events[6]["type"] == "episode_end"

        # All events should have same episode ID
        for event in events:
            assert event["id"] == ep_id
