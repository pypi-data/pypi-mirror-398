# chuk-gym-core

[![Test](https://github.com/chrishayuk/chuk-gym-core/actions/workflows/test.yml/badge.svg)](https://github.com/chrishayuk/chuk-gym-core/actions/workflows/test.yml)
[![PyPI version](https://badge.fury.io/py/chuk-gym-core.svg)](https://badge.fury.io/py/chuk-gym-core)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Shared infrastructure for building reasoning gym environments for training and evaluating AI reasoning capabilities.

## What is this?

**chuk-gym-core** is a Python library that provides the foundational components for creating **reasoning gym environments** - structured environments where AI models can practice and be evaluated on logical reasoning, mathematical problem-solving, and constraint satisfaction tasks.

Think of it like OpenAI Gym, but specifically designed for:
- **Training reasoning models** with step-by-step verification
- **Generating synthetic reasoning datasets** for fine-tuning LLMs
- **Evaluating AI reasoning capabilities** with partial credit scoring
- **Curriculum learning** that adapts difficulty based on performance

### Key Concepts

1. **Problems**: Self-contained reasoning challenges with prompts and gold answers
2. **Traces**: Machine-checkable solution traces showing each reasoning step
3. **Environments**: Async interfaces for interactive problem-solving with rewards
4. **Verification**: Automatic answer checking with error classification
5. **Curriculum**: Progressive difficulty scheduling for training

## Use Cases

- **Training Data Generation**: Generate millions of math/logic problems with verified solutions
- **RL Training**: Use environments with reward signals for reinforcement learning
- **Model Evaluation**: Test reasoning capabilities with partial credit and error analysis
- **Dataset Export**: Export to JSONL, chat, or instruction formats for fine-tuning

## Overview

`chuk-gym-core` provides the unified foundation for reasoning gym environments:

- **chuk-math-gym**: Mathematical reasoning environments (arithmetic, algebra, etc.)
- **puzzle-arcade-server**: Logic puzzle environments (sudoku, kenken, etc.)

Both projects share the same protocol, data formats, and can be served through the same infrastructure.

## Features

- **Pydantic-native**: All schemas use Pydantic v2 for validation and serialization
- **Async-native**: Environment interface is fully async for modern Python patterns
- **No magic strings**: Type-safe enums for difficulty levels, operations, error types
- **No dictionary goop**: Strongly-typed dataclasses and Pydantic models throughout
- **90%+ test coverage**: Comprehensive test suite with strict coverage requirements

## Installation

```bash
pip install chuk-gym-core
```

Or with uv:

```bash
uv pip install chuk-gym-core
```

For development:

```bash
pip install -e ".[dev]"
```

## Quick Start

### Creating a Problem

```python
from chuk_gym_core import Problem, DifficultyLevel, ToolPolicy

problem = Problem(
    id="arithmetic_easy_42",
    seed=42,
    domain="arithmetic",
    difficulty=DifficultyLevel.EASY,
    prompt="What is 3 + 5 * 2?",
    gold_answer="13",
    tool_policy=ToolPolicy.ALLOWED,
)
```

### Creating a Solution Trace

```python
from chuk_gym_core import Trace, Step, StepOperation, StepRef

trace = Trace(
    problem_id=problem.id,
    steps=[
        Step(
            index=0,
            operation=StepOperation.MULTIPLY,
            before_state="5 * 2",
            after_state="10",
            output_value=10,
            explanation="First, multiply 5 by 2",
        ),
        Step(
            index=1,
            operation=StepOperation.ADD,
            before_state="3 + 10",
            after_state="13",
            input_refs=[StepRef(step_index=0)],
            output_value=13,
            explanation="Then, add 3 to get the final answer",
        ),
    ],
)

# Verify the answer
assert trace.verify_final(13)
print(trace.to_natural_language())
```

### Implementing a Custom Environment

```python
from chuk_gym_core import ReasoningEnv, Problem, Trace, DifficultyLevel

class MyMathEnv(ReasoningEnv):
    @property
    def domain(self) -> str:
        return "my_math"

    async def _generate_problem(
        self, seed: int, difficulty: DifficultyLevel
    ) -> Problem:
        # Generate a problem based on seed and difficulty
        return Problem(
            id=f"math_{seed}",
            seed=seed,
            domain=self.domain,
            difficulty=difficulty,
            prompt="What is 2 + 2?",
            gold_answer="4",
        )

    async def _generate_trace(self, problem: Problem) -> Trace | None:
        # Generate the solution trace
        return Trace(
            problem_id=problem.id,
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

    async def _validate_action(self, action: str) -> tuple[bool, float, str]:
        # Validate and execute the action
        if action.strip() == "4":
            return True, 1.0, "Correct!"
        return False, 0.0, "Try again"

    def _is_complete(self) -> bool:
        # Check if the problem is solved
        return self.state and self.state.steps_taken > 0

    def _get_observation(self) -> dict:
        return {"prompt": self.state.problem.prompt if self.state else ""}


# Usage
async def main():
    env = MyMathEnv()
    obs, info = await env.reset(seed=42, difficulty=DifficultyLevel.EASY)
    print(f"Problem: {obs['prompt']}")

    obs, reward, terminated, truncated, info = await env.step("4")
    print(f"Result: {info['message']}, Reward: {reward}")
```

### Curriculum Learning

```python
from chuk_gym_core import (
    CurriculumScheduler,
    PerformanceBasedProgression,
    DifficultyLevel,
)

# Create a scheduler that advances when solve rate > 80%
scheduler = CurriculumScheduler(
    strategy=PerformanceBasedProgression(
        advance_threshold=0.8,
        retreat_threshold=0.3,
        min_episodes=20,
    ),
    start_difficulty=DifficultyLevel.EASY,
)

# Training loop
for episode in range(1000):
    difficulty = scheduler.get_current_difficulty()
    result = run_episode(env, difficulty)

    scheduler.record_episode(
        solved=result.success,
        steps=result.steps,
        invalid=result.invalid_actions,
        hints=result.hints_used,
        efficiency=result.efficiency,
    )

    if episode % 100 == 0:
        print(scheduler.get_summary())
```

### Dataset Export

```python
from chuk_gym_core import JSONLExporter, Problem, Trace

# Export problems and traces for training
with JSONLExporter("training_data.jsonl") as exporter:
    for problem, trace in generator.generate_batch(1000):
        exporter.write_problem(problem, trace)

# Export in chat format for fine-tuning
with JSONLExporter("chat_data.jsonl") as exporter:
    for problem, trace in generator.generate_batch(1000):
        exporter.write_training_example(problem, trace, format_type="chat")
```

### Episode Tracing

```python
from chuk_gym_core import EpisodeTracer, DifficultyLevel

# Trace episodes for offline analysis
with EpisodeTracer("traces.jsonl") as tracer:
    ep_id = tracer.start_episode(
        env_id="sudoku.v1",
        seed=42,
        difficulty=DifficultyLevel.MEDIUM,
        prompt="Solve this puzzle",
    )

    tracer.log_observation(state=grid, valid_actions=actions)
    tracer.log_action(action="place 1 5 7", success=True, reward=1.0)
    tracer.log_hint(hint="Try row 3", hints_remaining=4)

    tracer.end_episode(
        status="solved",
        moves=45,
        optimal_steps=40,
    )
```

## Core Types

### Difficulty Levels

7-level unified difficulty system:

| Level | Numeric | Description |
|-------|---------|-------------|
| `VERY_EASY` | 1 | Trivial, minimal reasoning |
| `EASY` | 2 | Simple, single-step |
| `PRETTY_EASY` | 3 | Slightly harder |
| `MEDIUM` | 4 | Moderate, multi-step |
| `HARD` | 5 | Challenging |
| `PRETTY_HARD` | 6 | Very challenging |
| `VERY_HARD` | 7 | Expert level |

### Tool Policy

```python
from chuk_gym_core import ToolPolicy, SolverConfig

# No tools allowed (pure reasoning)
config = SolverConfig.solver_free()

# Tools with budget and penalty
config = SolverConfig.solver_assisted(budget=10, penalty=0.1)

# Unlimited tools
config = SolverConfig.unlimited()
```

### Error Types

Type-safe error classification for analysis:

```python
from chuk_gym_core import ErrorType, VerificationResult

result = VerificationResult.failure(
    error_type=ErrorType.ORDER_OF_OPS,
    message="PEMDAS violation",
    expected=13,
    actual=16,
)
```

## Architecture

```
chuk-gym-core/
├── schemas/           # Pydantic models
│   ├── config.py      # DifficultyLevel, SolverConfig, ToolPolicy
│   ├── problem.py     # Problem
│   ├── trace.py       # Step, StepRef, StepOperation, Trace
│   ├── verification.py # VerificationResult, ErrorType
│   └── episode.py     # EpisodeRecord, EpisodeTracer
├── env/               # Environment interfaces
│   └── base.py        # ReasoningEnv (async ABC)
├── generators/        # Problem generator base
│   └── base.py        # ProblemGenerator (ABC)
├── verifiers/         # Answer verifier base
│   └── base.py        # Verifier (ABC)
├── curriculum/        # Difficulty scheduling
│   └── scheduler.py   # CurriculumScheduler, ProgressionStrategy
└── export/            # Dataset export
    ├── formats.py     # ExportFormat enum
    └── jsonl.py       # JSONLExporter
```

## Development

```bash
# Install dev dependencies
make dev-install

# Run tests
make test

# Run tests with coverage
make test-cov

# Run linting
make lint

# Format code
make format

# Run all checks
make check
```

## API Reference

### Schemas

- `Problem`: Canonical problem representation
- `Trace`: Machine-checkable solution trace
- `Step`: Single step in a solution
- `StepRef`: Type-safe reference to previous step
- `StepOperation`: Enum of step operations
- `VerificationResult`: Answer verification result
- `ErrorType`: Classification of errors
- `EpisodeRecord`: Complete episode for training/evaluation
- `EpisodeTracer`: JSONL episode logger

### Configuration

- `DifficultyLevel`: 7-level difficulty enum
- `DifficultyProfile`: Detailed difficulty characteristics
- `SolverConfig`: Tool/hint usage configuration
- `ToolPolicy`: Tool usage policy enum
- `OutputMode`: Server communication modes

### Environment

- `ReasoningEnv`: Abstract async environment base class
- `EpisodeState`: Current episode state dataclass

### Generators & Verifiers

- `ProblemGenerator`: Abstract problem generator
- `Verifier`: Abstract answer verifier

### Curriculum

- `CurriculumScheduler`: Main scheduler
- `ProgressionStrategy`: Abstract progression strategy
- `LinearProgression`: Fixed schedule progression
- `PerformanceBasedProgression`: Adaptive progression
- `StepBasedProgression`: Mastery-based progression

### Export

- `JSONLExporter`: JSONL dataset exporter
- `ExportFormat`: Supported export formats enum

## License

MIT
