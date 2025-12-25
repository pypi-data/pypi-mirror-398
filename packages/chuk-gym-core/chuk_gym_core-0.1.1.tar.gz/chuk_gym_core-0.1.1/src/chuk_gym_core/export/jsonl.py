"""
JSONL exporter for episode and problem data.
"""

import json
from pathlib import Path
from typing import Any, TextIO

from chuk_gym_core.schemas.episode import EpisodeRecord
from chuk_gym_core.schemas.problem import Problem
from chuk_gym_core.schemas.trace import Trace


class JSONLExporter:
    """
    Export problems, traces, and episodes to JSONL format.

    JSONL (JSON Lines) is ideal for:
    - Streaming large datasets
    - Appending new records
    - Line-by-line processing
    - Training data pipelines

    Usage:
        exporter = JSONLExporter("output.jsonl")

        for problem, trace in generator.generate_batch(100):
            exporter.write_problem(problem, trace)

        exporter.close()

    Or as context manager:
        with JSONLExporter("output.jsonl") as exporter:
            exporter.write_episode(episode)
    """

    def __init__(
        self,
        output: str | Path | TextIO,
        include_trace: bool = True,
        include_teacher_steps: bool = True,
    ):
        """
        Initialize the exporter.

        Args:
            output: Output file path or file handle
            include_trace: Whether to include solution traces
            include_teacher_steps: Whether to include teacher explanations
        """
        self._output: TextIO | None = None
        self._owns_file = False
        self.include_trace = include_trace
        self.include_teacher_steps = include_teacher_steps
        self._count = 0

        if isinstance(output, (str, Path)):
            self._output = open(output, "w", encoding="utf-8")
            self._owns_file = True
        else:
            self._output = output

    def __enter__(self) -> "JSONLExporter":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the output file if we own it."""
        if self._owns_file and self._output:
            self._output.close()
            self._output = None

    def _write_line(self, data: dict[str, Any]) -> None:
        """Write a single JSON line."""
        if self._output:
            self._output.write(json.dumps(data, default=str) + "\n")
            self._count += 1

    def write_problem(
        self,
        problem: Problem,
        trace: Trace | None = None,
    ) -> None:
        """
        Write a problem (and optional trace) to the output.

        Args:
            problem: The problem to write
            trace: Optional solution trace
        """
        data: dict[str, Any] = {
            "type": "problem",
            "id": problem.id,
            "domain": problem.domain,
            "difficulty": problem.difficulty.value,
            "seed": problem.seed,
            "prompt": problem.prompt,
        }

        if problem.expression:
            data["expression"] = problem.expression

        if problem.gold_answer:
            data["gold_answer"] = problem.gold_answer

        if problem.initial_state is not None:
            data["initial_state"] = problem.initial_state

        if problem.constraint_types:
            data["constraint_types"] = problem.constraint_types

        if self.include_trace and trace:
            data["trace"] = trace.to_jsonl_steps()
            data["optimal_steps"] = trace.total_steps

        self._write_line(data)

    def write_episode(self, episode: EpisodeRecord) -> None:
        """
        Write an episode record to the output.

        Args:
            episode: The episode record to write
        """
        data: dict[str, Any] = {
            "type": "episode",
            "episode_id": episode.episode_id,
            "env_id": episode.env_id,
            "domain": episode.domain,
            "difficulty": episode.difficulty.value,
            "seed": episode.seed,
            "prompt": episode.prompt,
            "status": episode.status.value,
            "success": episode.success,
            "steps_taken": episode.steps_taken,
            "invalid_actions": episode.invalid_actions,
            "hints_used": episode.hints_used,
            "efficiency_score": episode.efficiency_score,
            "wall_time_ms": episode.wall_time_ms,
        }

        if episode.optimal_steps:
            data["optimal_steps"] = episode.optimal_steps

        if episode.gold_answer:
            data["gold_answer"] = episode.gold_answer

        if episode.final_answer:
            data["final_answer"] = episode.final_answer

        # Include trajectory if available
        if episode.trajectory and self.include_teacher_steps:
            data["trajectory"] = [
                {
                    "t": step.t,
                    "action": step.action,
                    "reward": step.reward,
                    "teacher_steps": [s.model_dump() for s in step.teacher_steps]
                    if step.teacher_steps
                    else [],
                }
                for step in episode.trajectory
            ]

        self._write_line(data)

    def write_training_example(
        self,
        problem: Problem,
        trace: Trace,
        format_type: str = "qa",
    ) -> None:
        """
        Write a training example in a specific format.

        Args:
            problem: The problem
            trace: The solution trace
            format_type: Format type ('qa', 'chat', 'instruct')
        """
        data: dict[str, Any]
        if format_type == "qa":
            data = {
                "type": "training_qa",
                "question": problem.prompt,
                "answer": problem.gold_answer or str(trace.final_value),
                "steps": trace.to_natural_language(),
            }
        elif format_type == "chat":
            answer = problem.gold_answer or trace.final_value
            content = f"{trace.to_natural_language()}\n\nFinal answer: {answer}"
            data = {
                "type": "training_chat",
                "messages": [
                    {"role": "user", "content": problem.prompt},
                    {"role": "assistant", "content": content},
                ],
            }
        elif format_type == "instruct":
            answer = problem.gold_answer or trace.final_value
            output = f"{trace.to_natural_language()}\n\nAnswer: {answer}"
            data = {
                "type": "training_instruct",
                "instruction": f"Solve the following {problem.domain} problem step by step.",
                "input": problem.prompt,
                "output": output,
            }
        else:
            raise ValueError(f"Unknown format type: {format_type}")

        data["metadata"] = {
            "id": problem.id,
            "domain": problem.domain,
            "difficulty": problem.difficulty.value,
            "seed": problem.seed,
        }

        self._write_line(data)

    @property
    def count(self) -> int:
        """Number of records written."""
        return self._count

    def flush(self) -> None:
        """Flush the output buffer."""
        if self._output:
            self._output.flush()
