"""Tests for export/jsonl.py and export/formats.py."""

import json
from datetime import datetime
from io import StringIO
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from chuk_gym_core.export.formats import ExportFormat
from chuk_gym_core.export.jsonl import JSONLExporter
from chuk_gym_core.schemas.config import DifficultyLevel
from chuk_gym_core.schemas.episode import (
    EpisodeRecord,
    EpisodeStatus,
    MoveRecord,
    TrajectoryStep,
)
from chuk_gym_core.schemas.problem import Problem
from chuk_gym_core.schemas.trace import Step, StepOperation, Trace


class TestExportFormat:
    """Tests for ExportFormat enum."""

    def test_all_formats_exist(self):
        """Test all expected formats exist."""
        assert ExportFormat.JSONL == "jsonl"
        assert ExportFormat.JSON == "json"
        assert ExportFormat.CSV == "csv"
        assert ExportFormat.PARQUET == "parquet"
        assert ExportFormat.CHAT == "chat"
        assert ExportFormat.QA == "qa"
        assert ExportFormat.INSTRUCT == "instruct"
        assert ExportFormat.HF_DATASET == "hf_dataset"

    def test_format_values(self):
        """Test format string values."""
        assert ExportFormat.JSONL.value == "jsonl"
        assert ExportFormat.CHAT.value == "chat"


class TestJSONLExporter:
    """Tests for JSONLExporter."""

    @pytest.fixture
    def problem(self) -> Problem:
        return Problem(
            id="test_1",
            seed=42,
            domain="arithmetic",
            difficulty=DifficultyLevel.MEDIUM,
            prompt="What is 2 + 2?",
            expression="2 + 2",
            gold_answer="4",
            initial_state={"expression": "2 + 2"},
            constraint_types=["addition"],
        )

    @pytest.fixture
    def trace(self) -> Trace:
        return Trace(
            problem_id="test_1",
            steps=[
                Step(
                    index=0,
                    operation=StepOperation.ADD,
                    before_state="2 + 2",
                    after_state="4",
                    output_value=4,
                    explanation="Add 2 and 2 to get 4",
                )
            ],
        )

    @pytest.fixture
    def episode(self) -> EpisodeRecord:
        now = datetime.now()
        return EpisodeRecord(
            episode_id="ep_test_1",
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
            final_answer="4",
            gold_answer="4",
            steps_taken=1,
            invalid_actions=0,
            hints_used=0,
            optimal_steps=1,
            trajectory=[
                TrajectoryStep(
                    t=0,
                    observation={"state": "2 + 2"},
                    action="ANSWER 4",
                    reward=1.0,
                    next_observation={"state": "solved"},
                    done=True,
                    teacher_steps=[
                        Step(
                            index=0,
                            operation=StepOperation.ADD,
                            before_state="2 + 2",
                            after_state="4",
                            output_value=4,
                        )
                    ],
                )
            ],
            move_history=[
                MoveRecord(
                    step=0,
                    action="ANSWER 4",
                    success=True,
                    reward=1.0,
                )
            ],
        )

    def test_init_with_string_path(self):
        """Test initialization with string path."""
        with NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = f.name

        exporter = JSONLExporter(path)
        exporter.close()

        Path(path).unlink()

    def test_init_with_path_object(self):
        """Test initialization with Path object."""
        with NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = Path(f.name)

        exporter = JSONLExporter(path)
        exporter.close()

        path.unlink()

    def test_init_with_file_handle(self):
        """Test initialization with file handle."""
        output = StringIO()
        exporter = JSONLExporter(output)
        exporter.close()

    def test_context_manager(self, problem: Problem, trace: Trace):
        """Test context manager usage."""
        output = StringIO()

        with JSONLExporter(output) as exporter:
            exporter.write_problem(problem, trace)

        assert exporter.count == 1

    def test_write_problem(self, problem: Problem, trace: Trace):
        """Test write_problem."""
        output = StringIO()
        exporter = JSONLExporter(output)
        exporter.write_problem(problem, trace)
        exporter.close()

        output.seek(0)
        line = output.readline()
        data = json.loads(line)

        assert data["type"] == "problem"
        assert data["id"] == "test_1"
        assert data["domain"] == "arithmetic"
        assert data["difficulty"] == "medium"
        assert data["seed"] == 42
        assert data["prompt"] == "What is 2 + 2?"
        assert data["expression"] == "2 + 2"
        assert data["gold_answer"] == "4"
        assert data["initial_state"] == {"expression": "2 + 2"}
        assert data["constraint_types"] == ["addition"]
        assert "trace" in data
        assert data["optimal_steps"] == 1

    def test_write_problem_without_trace(self, problem: Problem):
        """Test write_problem without trace."""
        output = StringIO()
        exporter = JSONLExporter(output)
        exporter.write_problem(problem)
        exporter.close()

        output.seek(0)
        data = json.loads(output.readline())

        assert "trace" not in data
        assert "optimal_steps" not in data

    def test_write_problem_include_trace_false(self, problem: Problem, trace: Trace):
        """Test write_problem with include_trace=False."""
        output = StringIO()
        exporter = JSONLExporter(output, include_trace=False)
        exporter.write_problem(problem, trace)
        exporter.close()

        output.seek(0)
        data = json.loads(output.readline())

        assert "trace" not in data

    def test_write_problem_minimal(self):
        """Test write_problem with minimal problem."""
        problem = Problem(
            id="minimal",
            seed=1,
            domain="test",
            difficulty=DifficultyLevel.EASY,
            prompt="Minimal test",
        )

        output = StringIO()
        exporter = JSONLExporter(output)
        exporter.write_problem(problem)
        exporter.close()

        output.seek(0)
        data = json.loads(output.readline())

        assert data["id"] == "minimal"
        assert "expression" not in data
        assert "gold_answer" not in data

    def test_write_episode(self, episode: EpisodeRecord):
        """Test write_episode."""
        output = StringIO()
        exporter = JSONLExporter(output)
        exporter.write_episode(episode)
        exporter.close()

        output.seek(0)
        data = json.loads(output.readline())

        assert data["type"] == "episode"
        assert data["episode_id"] == "ep_test_1"
        assert data["env_id"] == "arithmetic.v1"
        assert data["domain"] == "arithmetic"
        assert data["difficulty"] == "medium"
        assert data["status"] == "solved"
        assert data["success"] is True
        assert data["steps_taken"] == 1
        assert data["efficiency_score"] == 1.0
        assert "trajectory" in data

    def test_write_episode_without_trajectory(self):
        """Test write_episode without trajectory."""
        now = datetime.now()
        episode = EpisodeRecord(
            episode_id="ep_test",
            env_id="test.v1",
            instance_id="test",
            domain="test",
            difficulty=DifficultyLevel.EASY,
            seed=1,
            prompt="Test",
            started_at=now,
            ended_at=now,
            wall_time_ms=500,
            status=EpisodeStatus.FAILED,
            steps_taken=5,
            invalid_actions=2,
            hints_used=0,
        )

        output = StringIO()
        exporter = JSONLExporter(output)
        exporter.write_episode(episode)
        exporter.close()

        output.seek(0)
        data = json.loads(output.readline())

        assert "trajectory" not in data
        assert data["success"] is False

    def test_write_episode_include_teacher_steps_false(self, episode: EpisodeRecord):
        """Test write_episode with include_teacher_steps=False."""
        output = StringIO()
        exporter = JSONLExporter(output, include_teacher_steps=False)
        exporter.write_episode(episode)
        exporter.close()

        output.seek(0)
        data = json.loads(output.readline())

        assert "trajectory" not in data

    def test_write_training_example_qa(self, problem: Problem, trace: Trace):
        """Test write_training_example with QA format."""
        output = StringIO()
        exporter = JSONLExporter(output)
        exporter.write_training_example(problem, trace, format_type="qa")
        exporter.close()

        output.seek(0)
        data = json.loads(output.readline())

        assert data["type"] == "training_qa"
        assert data["question"] == "What is 2 + 2?"
        assert data["answer"] == "4"
        assert "steps" in data
        assert data["metadata"]["id"] == "test_1"
        assert data["metadata"]["domain"] == "arithmetic"
        assert data["metadata"]["difficulty"] == "medium"
        assert data["metadata"]["seed"] == 42

    def test_write_training_example_chat(self, problem: Problem, trace: Trace):
        """Test write_training_example with chat format."""
        output = StringIO()
        exporter = JSONLExporter(output)
        exporter.write_training_example(problem, trace, format_type="chat")
        exporter.close()

        output.seek(0)
        data = json.loads(output.readline())

        assert data["type"] == "training_chat"
        assert "messages" in data
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][1]["role"] == "assistant"
        assert "Final answer: 4" in data["messages"][1]["content"]

    def test_write_training_example_instruct(self, problem: Problem, trace: Trace):
        """Test write_training_example with instruct format."""
        output = StringIO()
        exporter = JSONLExporter(output)
        exporter.write_training_example(problem, trace, format_type="instruct")
        exporter.close()

        output.seek(0)
        data = json.loads(output.readline())

        assert data["type"] == "training_instruct"
        assert "instruction" in data
        assert "arithmetic" in data["instruction"]
        assert data["input"] == "What is 2 + 2?"
        assert "Answer: 4" in data["output"]

    def test_write_training_example_invalid_format(self, problem: Problem, trace: Trace):
        """Test write_training_example with invalid format."""
        output = StringIO()
        exporter = JSONLExporter(output)

        with pytest.raises(ValueError, match="Unknown format type"):
            exporter.write_training_example(problem, trace, format_type="invalid")

    def test_count_property(self, problem: Problem, trace: Trace):
        """Test count property."""
        output = StringIO()
        exporter = JSONLExporter(output)

        assert exporter.count == 0

        exporter.write_problem(problem, trace)
        assert exporter.count == 1

        exporter.write_problem(problem, trace)
        assert exporter.count == 2

        exporter.close()

    def test_flush(self, problem: Problem, trace: Trace):
        """Test flush method."""
        output = StringIO()
        exporter = JSONLExporter(output)
        exporter.write_problem(problem, trace)
        exporter.flush()

        output.seek(0)
        assert len(output.readline()) > 0

        exporter.close()

    def test_multiple_records(self, problem: Problem, trace: Trace):
        """Test writing multiple records."""
        output = StringIO()
        exporter = JSONLExporter(output)

        for i in range(5):
            p = Problem(
                id=f"test_{i}",
                seed=i,
                domain="test",
                difficulty=DifficultyLevel.EASY,
                prompt=f"Problem {i}",
            )
            exporter.write_problem(p)

        exporter.close()

        output.seek(0)
        lines = output.readlines()
        assert len(lines) == 5

        for i, line in enumerate(lines):
            data = json.loads(line)
            assert data["id"] == f"test_{i}"

    def test_write_problem_with_none_values(self):
        """Test write_problem handles None values correctly."""
        problem = Problem(
            id="test",
            seed=1,
            domain="test",
            difficulty=DifficultyLevel.EASY,
            prompt="Test",
            expression=None,
            gold_answer=None,
            initial_state=None,
        )

        output = StringIO()
        exporter = JSONLExporter(output)
        exporter.write_problem(problem)
        exporter.close()

        output.seek(0)
        data = json.loads(output.readline())

        assert "expression" not in data
        assert "gold_answer" not in data
        assert "initial_state" not in data


class TestJSONLExporterFileOperations:
    """Tests for JSONLExporter file operations."""

    def test_write_to_file(self):
        """Test writing to actual file."""
        with NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = f.name

        problem = Problem(
            id="file_test",
            seed=1,
            domain="test",
            difficulty=DifficultyLevel.EASY,
            prompt="File test",
        )

        with JSONLExporter(path) as exporter:
            exporter.write_problem(problem)

        # Read and verify
        with open(path, "r") as f:
            data = json.loads(f.readline())

        assert data["id"] == "file_test"

        Path(path).unlink()

    def test_close_idempotent(self):
        """Test that close can be called multiple times."""
        output = StringIO()
        exporter = JSONLExporter(output)
        exporter.close()
        exporter.close()  # Should not raise

    def test_write_after_close_file(self):
        """Test that write after close to file does nothing."""
        with NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = f.name

        exporter = JSONLExporter(path)
        exporter.close()

        # After close, _output is None, so write does nothing
        problem = Problem(
            id="test",
            seed=1,
            domain="test",
            difficulty=DifficultyLevel.EASY,
            prompt="Test",
        )
        exporter.write_problem(problem)

        # File should be empty
        with open(path, "r") as f:
            assert f.read() == ""

        Path(path).unlink()
