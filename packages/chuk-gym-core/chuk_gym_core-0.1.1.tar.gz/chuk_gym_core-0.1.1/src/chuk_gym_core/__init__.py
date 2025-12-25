"""
chuk-gym-core: Shared infrastructure for reasoning gym environments.

This package provides the unified foundation for both:
- chuk-math-gym: Mathematical reasoning environments
- puzzle-arcade-server: Logic puzzle environments

Core components:
- Schemas: Unified data models (Problem, Trace, Step, Episode)
- Environment: Abstract ReasoningEnv base class
- Generators: Problem generator base class
- Verifiers: Answer verification base class
- Curriculum: Difficulty progression strategies
- Export: Dataset export utilities

Example usage:
    from chuk_gym_core import (
        ReasoningEnv,
        Problem,
        Trace,
        Step,
        DifficultyLevel,
        SolverConfig,
    )

    # Create a custom environment
    class MyEnv(ReasoningEnv):
        domain = "my_domain"
        ...

    # Use unified schemas
    problem = Problem(
        id="test_1",
        seed=42,
        domain="arithmetic",
        difficulty=DifficultyLevel.MEDIUM,
        prompt="What is 2 + 2?",
        gold_answer="4",
    )
"""

__version__ = "0.1.0"

# Schemas - Config
# Curriculum
from chuk_gym_core.curriculum.scheduler import (
    CurriculumScheduler,
    LinearProgression,
    PerformanceBasedProgression,
    PerformanceMetrics,
    ProgressionStrategy,
    StepBasedProgression,
)

# Environment
from chuk_gym_core.env.base import EpisodeState, ReasoningEnv

# Export
from chuk_gym_core.export.formats import ExportFormat
from chuk_gym_core.export.jsonl import JSONLExporter

# Generators
from chuk_gym_core.generators.base import ProblemGenerator
from chuk_gym_core.schemas.config import (
    DifficultyLevel,
    DifficultyProfile,
    OutputMode,
    SolverConfig,
    ToolPolicy,
)

# Schemas - Episode
from chuk_gym_core.schemas.episode import (
    EpisodeRecord,
    EpisodeStatus,
    EpisodeTracer,
    MoveRecord,
    TraceEvent,
    TrajectoryStep,
)

# Schemas - Problem
from chuk_gym_core.schemas.problem import Problem

# Schemas - Trace
from chuk_gym_core.schemas.trace import (
    Step,
    StepOperation,
    StepRef,
    Trace,
)

# Schemas - Verification
from chuk_gym_core.schemas.verification import (
    ErrorType,
    ToolCallGrade,
    VerificationResult,
)

# Verifiers
from chuk_gym_core.verifiers.base import Verifier

__all__ = [
    # Version
    "__version__",
    # Config
    "DifficultyLevel",
    "DifficultyProfile",
    "OutputMode",
    "SolverConfig",
    "ToolPolicy",
    # Problem
    "Problem",
    # Trace
    "Step",
    "StepOperation",
    "StepRef",
    "Trace",
    # Verification
    "ErrorType",
    "ToolCallGrade",
    "VerificationResult",
    # Episode
    "EpisodeRecord",
    "EpisodeStatus",
    "EpisodeTracer",
    "MoveRecord",
    "TraceEvent",
    "TrajectoryStep",
    # Environment
    "EpisodeState",
    "ReasoningEnv",
    # Generators
    "ProblemGenerator",
    # Verifiers
    "Verifier",
    # Curriculum
    "CurriculumScheduler",
    "LinearProgression",
    "PerformanceBasedProgression",
    "PerformanceMetrics",
    "ProgressionStrategy",
    "StepBasedProgression",
    # Export
    "ExportFormat",
    "JSONLExporter",
]
